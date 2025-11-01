"""
FastAPI Application - Travel Insurance Chatbot API
Simple API that exposes conversation agent with full message history
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import uvicorn
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add agent paths
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')

# Import Google ADK components
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import conversation agent
from agents.Conversation_agent.agent import conversation_agent, APP_NAME

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Travel Insurance Chatbot API",
    description="AI-powered travel insurance assistant - Returns full message history",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session service and runners
session_service = InMemorySessionService()
user_runners: Dict[str, Runner] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    messages: List[Message]  # Full conversation history
    user_id: str
    session_id: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_or_create_runner(user_id: str, session_id: str) -> Runner:
    """Get existing runner or create new one for user session"""
    session_key = f"{user_id}:{session_id}"

    if session_key not in user_runners:
        # Create new session
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # Create runner
        runner = Runner(
            agent=conversation_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        user_runners[session_key] = runner

    return user_runners[session_key]


async def get_session_messages(user_id: str, session_id: str) -> List[Message]:
    """
    Extract full message history from the session

    This reads the conversation history stored by Google ADK
    and converts it to a simple message list format
    """
    try:
        # Get the session from the service
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        messages = []

        # Extract conversation history from session
        if hasattr(session, 'history') and session.history:
            for item in session.history:
                # Handle Content objects
                if hasattr(item, 'role') and hasattr(item, 'parts'):
                    role = item.role if item.role in ['user', 'model'] else 'assistant'
                    # Map 'model' to 'assistant' for consistency
                    if role == 'model':
                        role = 'assistant'

                    # Extract text from parts
                    content = ''
                    if item.parts:
                        for part in item.parts:
                            if hasattr(part, 'text'):
                                content += part.text

                    if content:
                        messages.append(Message(role=role, content=content))

        return messages

    except Exception as e:
        # If session doesn't exist yet or error, return empty
        return []


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Travel Insurance AI Backend",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat - Send message to agent",
            "clear": "DELETE /session/{user_id}/{session_id} - Clear conversation"
        }
    }


@app.post("/chat")
async def chat(
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Main chat endpoint - send message and get full conversation history
    Can optionally include a file (passport, itinerary, etc.)

    Flow:
    1. Append user message (+file if provided) to session
    2. Agent processes and responds
    3. Return FULL message history (user + assistant messages)

    Args:
        user_id: User identifier
        message: User's message text
        session_id: Optional session ID
        file: Optional file upload (PNG, PDF, etc.)

    Returns:
        ChatResponse with full messages array and session info
    """
    try:
        session_id = session_id or f"session_{user_id}"

        # Set user_id in environment for sub-agent tools to access
        os.environ['CURRENT_USER_ID'] = user_id

        # Get or create runner for this session
        runner = await get_or_create_runner(user_id, session_id)

        # ========================================================================
        # PRE-PROCESSING: Auto-call fill_information for text messages
        # This ensures contact info and other details are saved before agent processes
        # ========================================================================
        if not file and message:  # Text message (no file upload)
            # Check if message contains substantive information (not just greetings)
            keywords = ['email', 'phone', 'address', 'live', '@', '+', 'street', 'road', 'singapore', 'city']
            has_info = any(keyword in message.lower() for keyword in keywords)

            if has_info:
                print(f"[PRE-PROCESSING] Detected information in text message, auto-calling fill_information...")
                from agents.Conversation_agent.tools import fill_information

                fill_result = fill_information(user_id, message)
                print(f"[PRE-PROCESSING] fill_information result: {fill_result.get('extracted_fields', {})}")
        # ========================================================================

        # Create content message for agent
        parts = [types.Part(text=message)]

        # If file is provided, add it to the message
        if file:
            file_contents = await file.read()
            mime_type = file.content_type or "application/octet-stream"

            # Add file part directly (no base64!)
            file_part = types.Part.from_bytes(
                data=file_contents,
                mime_type=mime_type
            )
            parts.append(file_part)

        content = types.Content(role='user', parts=parts)

        # Run agent and collect response
        final_response = "Agent did not produce a response."

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                elif getattr(event, 'actions', None) and event.actions.escalate:
                    final_response = f"Error: {event.error_message or 'Agent encountered an issue.'}"
                break

        # ========================================================================
        # AUTOMATIC PIPELINE MIDDLEWARE
        # After document extraction OR info collection, check if ready for policy recommendations
        # Only trigger when we have ALL required fields for quote/purchase
        # ========================================================================
        print("[MIDDLEWARE] Checking profile completeness...")
        from profile_manager import load_profile

        profile = load_profile(user_id)

        # Check COMPLETE requirements for pricing + purchase APIs
        # Trip info (for pricing API)
        has_trip_info = all([
            profile.get('tripType'),
            profile.get('departureDate'),
            profile.get('returnDate'),
            profile.get('departureCountry'),
            profile.get('arrivalCountry'),
            profile.get('adultsCount') is not None
        ])

        # Personal info (first insured - for purchase API)
        # Don't check email/phone here - those are contact fields checked below
        insureds = profile.get('insureds', [])
        has_personal_info = False
        if insureds and len(insureds) > 0:
            insured = insureds[0]
            has_personal_info = all([
                insured.get('title'),
                insured.get('firstName'),
                insured.get('lastName'),
                insured.get('nationality'),
                insured.get('dateOfBirth'),
                insured.get('passport')
            ])

        # Contact info (for purchase API)
        contact = profile.get('mainContact', {})
        has_contact_info = all([
            contact.get('email'),
            contact.get('phoneNumber'),
            contact.get('address'),
            contact.get('city'),
            contact.get('zipCode'),
            contact.get('countryCode')
        ])

        profile_complete = has_trip_info and has_personal_info and has_contact_info

        print(f"[MIDDLEWARE] Profile status: trip_info={has_trip_info}, personal_info={has_personal_info}, contact_info={has_contact_info}, complete={profile_complete}")

        if profile_complete:
            print(f"[MIDDLEWARE] Profile COMPLETE! Auto-triggering policy_recommendation_agent...")

            # Create a new message to trigger policy recommendations
            trigger_message = types.Content(
                role='user',
                parts=[types.Part(text=f"Based on my trip to {profile.get('arrivalCountry')} on {profile.get('departureDate')}, what insurance options do you recommend?")]
            )

            # Run agent again to get policy recommendations
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=trigger_message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        policy_response = event.content.parts[0].text
                        # Combine extraction + policy recommendation responses
                        final_response = f"{final_response}\n\n{policy_response}"
                        print("[MIDDLEWARE] Policy recommendations added to response!")
                    break
        elif has_trip_info and not profile_complete:
            # Profile not complete - agent should ask for missing info
            print("[MIDDLEWARE] Profile incomplete - agent should collect remaining fields")

        # ========================================================================

        # Get FULL message history from session
        messages = await get_session_messages(user_id, session_id)

        # If we couldn't extract from session, manually build the latest exchange
        if not messages or len(messages) < 2:
            messages = [
                Message(role="user", content=message),
                Message(role="assistant", content=final_response)
            ]

        return {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "user_id": user_id,
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.delete("/session/{user_id}/{session_id}")
async def clear_session(user_id: str, session_id: str):
    """
    Clear a user session (delete conversation history)

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        Success confirmation
    """
    try:
        session_key = f"{user_id}:{session_id}"

        # Remove from runner cache
        if session_key in user_runners:
            del user_runners[session_key]

        # Delete session from service
        try:
            await session_service.delete_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
        except:
            pass  # Session might not exist

        return {
            "success": True,
            "message": f"Session {session_id} cleared for user {user_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session clear error: {str(e)}")


# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
