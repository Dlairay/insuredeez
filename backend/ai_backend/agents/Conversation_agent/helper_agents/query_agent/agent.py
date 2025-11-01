"""
Query Agent
Answers questions about policy plans using Taxonomy_Filled.json
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import compare_plans, answer_policy_question
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the query agent using the base factory
query_agent = create_agent(
    name="query",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[compare_plans, answer_policy_question]
)
