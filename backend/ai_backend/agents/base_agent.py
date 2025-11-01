"""
Base Agent Factory for Google ADK Agents
Provides a common pattern for creating agents to reduce code duplication
"""

from google.adk.agents import Agent

# Default model for all agents - can be easily changed here
AGENT_MODEL = "gemini-2.0-flash"

def create_agent(
    name: str,
    description: str,
    instruction: str = None,
    tools: list = None,
    sub_agents: list = None,
    model: str = None
) -> Agent:
    """
    Factory function to create Google ADK agents with sensible defaults

    Args:
        name: Agent name identifier
        description: Short description of what the agent does
        instruction: Detailed instructions for the agent's behavior (optional)
        tools: List of tool functions the agent can use (optional)
        sub_agents: List of sub-agents for hierarchical agents (optional)
        model: Override the default model if needed (optional)

    Returns:
        Configured Google ADK Agent instance
    """

    # Use provided instruction or generate a default one
    if instruction is None:
        instruction = f"You are the {name} agent. {description}. Perform your tasks efficiently and accurately."

    return Agent(
        name=name,
        model=model or AGENT_MODEL,
        description=description,
        instruction=instruction,
        tools=tools or [],
        sub_agents=sub_agents or []
    )