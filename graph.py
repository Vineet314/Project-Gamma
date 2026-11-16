from langgraph.graph import StateGraph, START, END

from state import StockAnalysisState
from agents.supervisor import supervisor_agent
from agents.financial import financial_agent
from agents.technical import technical_agent

def should_continue(agent_state: StockAnalysisState) -> list[str]:
    return agent_state['next_agents']

builder = StateGraph(StockAnalysisState)
builder.add_node('supervisor_agent',supervisor_agent)
builder.add_node('financial_agent',financial_agent)
builder.add_node('technical_agent',technical_agent)

builder.add_edge(START, 'supervisor_agent')
builder.add_conditional_edges('supervisor_agent', should_continue)
builder.add_edge('financial_agent', END)
builder.add_edge('technical_agent', END)

graph = builder.compile()

config = {"configurable": {"thread_id": "multi-agent-1"}}
