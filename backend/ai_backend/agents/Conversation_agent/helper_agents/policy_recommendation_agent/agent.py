"""
Policy Recommendation Agent
Orchestrates needs, coverage, and plan selection to recommend the best insurance plan
"""

import sys
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend/agents')

from base_agent import create_agent
from .tools import consolidate_recommendation
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Import the three sub-agents
from .helper_agents.needs_agent.agent import needs_agent
from .helper_agents.coverage_recommendatio_agent.agent import coverage_agent
from .helper_agents.plan_selector_agent.agent import plan_selector_agent

# Create the policy recommendation agent with its three sub-agents
policy_recommendation_agent = create_agent(
    name="policy_recommendation",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    tools=[consolidate_recommendation],
    sub_agents=[needs_agent, coverage_agent, plan_selector_agent]
)
