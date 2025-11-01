"""
Coverage Recommendation Agent
Analyzes claims history to suggest coverage amounts
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import recommend_coverage
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the coverage recommendation agent using the base factory
coverage_agent = create_agent(
    name="coverage_recommendation",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[recommend_coverage]
)
