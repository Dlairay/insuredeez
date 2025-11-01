"""
FastAPI Application - Travel Insurance Chatbot
Simple API with just chat and user check endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import uvicorn
from pathlib import Path

# Import the conversation agent from the correct location
# Note: We'll integrate this with Google ADK agent later
# For now, using a placeholder import structure
import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

# Temporarily commenting out until we create the FastAPI integration layer
# from agents.Conversation_agent.agent import conversation_agent

# Initialize FastAPI app
app = FastAPI(title="Travel Insurance Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store agent instances per user
# agents: Dict[str, ConversationalAgent] = {}
# storage = JSONStorage()

# Temporary: Simple in-memory storage for demo
user_sessions = {}


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    user_id: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    needs_extracted: bool
    data: Dict


# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - send message, get response"""
    try:
        user_id = request.user_id

        # Get or create agent for this user
        if user_id not in agents:
            agents[user_id] = ConversationalAgent(user_id=user_id)

        agent = agents[user_id]
        result = agent.chat(user_message=request.message)

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/exists")
async def check_user_exists(user_id: str):
    """Check if user profile exists"""
    try:
        exists = user_id in user_sessions

        return {
            "user_id": user_id,
            "exists": exists,
            "message_count": len(user_sessions.get(user_id, {}).get("messages", []))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-payment")
async def process_payment(user_id: str, amount: float):
    """
    Mock payment processing endpoint
    Always returns success for development/testing purposes
    """
    import uuid

    return {
        "status": "success",
        "transaction_id": f"mock-txn-{uuid.uuid4().hex[:8]}",
        "amount": amount,
        "user_id": user_id,
        "payment_method": "mock",
        "message": "Payment processed successfully (MOCK)"
    }


# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
