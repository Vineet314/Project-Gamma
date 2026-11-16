
from typing import Any


def supervisor(state: dict[str, Any]) -> dict[str, Any]:
    """
    Rule-based supervisor.
    Determines which agents should execute.
    Later, it will be an LLM based agent.
    """

    analysis_type = state["analysis_type"]

    if analysis_type == "fundamental":
        next_agents = ["financial_agent"]

    elif analysis_type == "technical":
        next_agents = ["technical_agent"]

    elif analysis_type == "full":
        next_agents = ["financial_agent", "technical_agent"]

    else:
        raise ValueError(f"Unsupported analysis type: {analysis_type}")

    return {"next_agents": next_agents} # state update: give list of next agent/s to call