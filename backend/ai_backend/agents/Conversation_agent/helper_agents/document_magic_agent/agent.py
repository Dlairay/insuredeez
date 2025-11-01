"""
Document Magic Agent
Extracts travel information from uploaded documents (passport, ID, itinerary)
Uses its OWN vision capability to see images, then saves via tool
"""

from google.adk.agents import Agent
from .tools_new import save_document_data
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION_NEW

# Create the document magic agent - uses vision + save tool
document_magic_agent = Agent(
    name="document_magic",
    model="gemini-2.0-flash-exp",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION_NEW,
    tools=[save_document_data]
)
