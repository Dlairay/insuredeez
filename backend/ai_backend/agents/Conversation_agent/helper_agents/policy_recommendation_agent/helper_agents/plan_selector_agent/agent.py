"""
Plan Selector Agent
Selects the best insurance plan (A, B, or C) based on needs and coverage
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import select_best_plan
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the plan selector agent using the base factory
plan_selector_agent = create_agent(
    name="plan_selector",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[select_best_plan]
)
