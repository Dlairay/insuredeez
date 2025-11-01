"""
Document Magic Agent
Extracts travel information from uploaded documents (passport, ID, itinerary)
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import extract_and_fill_profile
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the document magic agent using the base factory
document_magic_agent = create_agent(
    name="document_magic",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[extract_and_fill_profile]
)
