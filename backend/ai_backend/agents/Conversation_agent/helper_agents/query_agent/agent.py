"""
Query Agent
Answers questions about policy plans using Taxonomy_Filled.json
"""

from google.adk.agents import Agent
from .tools import compare_plans, answer_policy_question
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the query agent directly
query_agent = Agent(
    name="query",
    model="gemini-2.0-flash-exp",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[compare_plans, answer_policy_question]
)
