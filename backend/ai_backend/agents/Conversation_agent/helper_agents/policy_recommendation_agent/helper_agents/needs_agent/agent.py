"""
Needs Agent
Analyzes itinerary to identify insurance needs
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import analyze_itinerary_needs
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the needs agent using the base factory
needs_agent = create_agent(
    name="needs",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[analyze_itinerary_needs]
)
