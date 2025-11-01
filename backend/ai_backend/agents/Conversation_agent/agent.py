
import asyncio
import os

# Import Google ADK components (not genai directly)
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import warnings
import logging
from dotenv import load_dotenv
import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from tools import get_user_data, fill_information, call_pricing_api, call_purchase_api
from prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

#just makes the output less messy
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('google').setLevel(logging.CRITICAL)
logging.getLogger('google_genai').setLevel(logging.CRITICAL)

load_dotenv()

# Configure logging to suppress warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

# Set environment variable for Google API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Import helper agents
from helper_agents.document_magic_agent.agent import document_magic_agent
from helper_agents.policy_recommendation_agent.agent import policy_recommendation_agent
from helper_agents.query_agent.agent import query_agent

# Create the main conversation agent using the base factory
conversation_agent = create_agent(
    name="conversation",
    description="Travel insurance assistant that helps users find and buy insurance plans",
    instruction=AGENT_INSTRUCTION,
    tools=[get_user_data, fill_information, call_pricing_api, call_purchase_api],
    sub_agents=[document_magic_agent, policy_recommendation_agent, query_agent]
)

# --- Session constants, needed to even run the agent even if its not used ---
APP_NAME = "insurance_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# --- Single call via Runner (same event loop pattern) ---
async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str):
    print(f"\n>>> User Query: {query}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response = "Agent did not produce a final response."

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            elif getattr(event, 'actions', None) and event.actions.escalate:
                final_response = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response}")

# --- Main: create session, create runner, run interactive loop ---
async def main():
    # Session service + session (this gives you the Session ID memory container)
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

    # Runner (execution engine that reads/writes session and calls tools)
    runner = Runner(
        agent=conversation_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    print("🛡️  Travel Insurance Assistant Started!")
    print("Ask me about travel insurance plans, upload documents, or get policy recommendations.")
    print("Type 'quit' to exit.")

    # Interactive chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check if user wants to quit
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thanks for using the Travel Insurance Assistant! Goodbye!")
                break

            # Skip empty inputs
            if not user_input:
                print("Please enter a message or 'quit' to exit.\n")
                continue

            # Call the agent with user input
            await call_agent_async(user_input, runner, USER_ID, SESSION_ID)
            print()  # Add spacing between conversations

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.\n")

if __name__ == "__main__":
    asyncio.run(main())
