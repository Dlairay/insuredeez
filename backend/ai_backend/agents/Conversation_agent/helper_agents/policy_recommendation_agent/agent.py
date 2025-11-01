"""
Policy Recommendation Agent
Has 3 tools: analyze needs (2-stage + DB), recommend coverage (real DB), select plan (taxonomy)
"""

from google.adk.agents import Agent
from .tools import analyze_itinerary_needs, recommend_coverage, select_best_plan
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Create the policy recommendation agent with all 3 tools (no sub-agents)
policy_recommendation_agent = Agent(
    name="policy_recommendation",
    model="gemini-2.0-flash-exp",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[analyze_itinerary_needs, recommend_coverage, select_best_plan]
)
