# this v1 has (no cumulative messages, no interrupts)
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage 
from langgraph.graph import StateGraph, START, END
from typing import Any, TypedDict

from single_agent.agent import llm_with_python
from tools.py_tool import execute_python_code
SYSTEM_PROMPT = 'You have a tool available to you, named execute_python_code, which provides you with a python envieronment, which has a df loaded in it, with the name `df`.'

# Tool Registary
ALL_TOOLS = [execute_python_code]
TOOLS = {tool.name:tool for tool in ALL_TOOLS}

# --------------------------- State ------------------------------------------
class AgentState(TypedDict): # state schema
    messages: list[BaseMessage]
    python_policy: str
    pending_tool_calls: list

# --------------------------- Util functions------------------------------------------
def execute_tool(tool_call: dict[str, Any]) -> ToolMessage:
    ''' Executes a tool, returns the output in a ToolMessage object'''
    
    tool = TOOLS.get(tool_call['name'])

    if tool is None: 
        raise ValueError(f"Unkown tool: {tool_call['name']}")
    try:
        result = tool.invoke(tool_call['args'])
    except Exception as e:
        result = "Tool execution failed.\n" \
        f"Error type: {type(e).__name__}\n" \
        f"Error: {e}"

    return ToolMessage(content=str(result), tool_call_id = tool_call['id'])

def show_flow(agent_state:AgentState) -> None:
    print()
    for msg in agent_state['messages']:
        if isinstance(msg, SystemMessage): continue
        print(type(msg).__name__)
        if isinstance(msg, AIMessage): 
            for call in msg.tool_calls:
                print(call['name'], call['args'])
        print(msg.content)
        print("-" * 80)

# --------------------------- Nodes ------------------------------------------
def planner(agent_state:AgentState) -> AgentState:
    ''' Think and append AIMessage '''
    
    response:AIMessage = llm_with_python.invoke(agent_state['messages'])
    agent_state['messages'].append(response)
    agent_state['pending_tool_calls'] = response.tool_calls
    if not response.tool_calls: print(f"AI: {response.content}")
    return agent_state

def tool_executor(agent_state:AgentState) -> AgentState:
    ''' Execute every requested tool, append ToolMessage '''

    for tool_call in agent_state["pending_tool_calls"]:
        if tool_call['name'] == 'execute_python_code' and agent_state['python_policy'] == 'ask':

            approval = input(
                f"\nLLM wants to execute:\n\n"
                f"{tool_call['args']['code']}\n\n"
                "Approve (Y/N) or Approve always (A): ")

            while approval.upper() not in ("Y", "N", "A"):
                approval = input("Approve (Y/N) or Approve always (A): ")

            if approval.upper() == "N":
                agent_state["messages"].append(
                    ToolMessage(content="User denied Python execution.",tool_call_id=tool_call["id"]))
                continue
            
            elif approval.upper() == 'A':
                agent_state['python_policy'] = 'allow'

        tool_response = execute_tool(tool_call)    
        agent_state['messages'].append(tool_response)

    agent_state['pending_tool_calls'] = []
    return agent_state

def should_continue(agent_state: AgentState) -> str:

    return "tool_executor" if agent_state["pending_tool_calls"] else END

# --------------------------- State ------------------------------------------

builder = StateGraph(AgentState)

builder.add_node('planner',planner)
builder.add_node('tool_executor',tool_executor)

builder.add_edge(START, 'planner')
builder.add_edge('tool_executor', 'planner')

builder.add_conditional_edges('planner', should_continue, {"tool_executor":"tool_executor", END:END})

graph = builder.compile()

agent_state: AgentState = {
    "messages": [SystemMessage(content=SYSTEM_PROMPT)],
    "python_policy": "ask",
    "pending_tool_calls": []}

while True:
    text = input("Human: ")

    if text.lower().strip() in ("quit", "exit", "bye"):
        break

    agent_state["messages"].append(HumanMessage(content=text))

    agent_state = graph.invoke(agent_state)



def tool_executor(agent_state:AgentState) -> AgentState:
    ''' Execute every requested tool, append ToolMessage '''
    new_messages = []
    python_policy = agent_state['python_policy']

    for tool_call in agent_state["pending_tool_calls"]:
        if tool_call['name'] == 'execute_python_code' and agent_state['python_policy'] == 'ask':

            approval = input(
                f"\nLLM wants to execute:\n\n"
                f"{tool_call['args']['code']}\n\n"
                "Approve (Y/N) or Approve always (A): ")

            while approval.upper() not in ("Y", "N", "A"):
                approval = input("Approve (Y/N) or Approve always (A): ")

            if approval.upper() == "N":
                agent_state["messages"].append(
                    ToolMessage(content="User denied Python execution.",tool_call_id=tool_call["id"]))
                continue
            
            elif approval.upper() == 'A':
                agent_state['python_policy'] = 'allow'

        tool_response = execute_tool(tool_call)    
        agent_state['messages'].append(tool_response)

    agent_state['pending_tool_calls'] = []
    return agent_state

def tool_executor(state: AgentState) -> dict:
    """Execute every requested tool and return state updates."""

    new_messages = []
    python_policy = state["python_policy"]

    for tool_call in state["pending_tool_calls"]:

        if tool_call["name"] == "execute_python_code" and python_policy == "ask":

            approval = input(
                f"\nLLM wants to execute:\n\n"
                f"{tool_call['args']['code']}\n\n"
                "Approve (Y/N) or Approve always (A): ")

            while approval.upper() not in ("Y", "N", "A"):
                approval = input("Approve (Y/N) or Approve always (A): ")

            if approval.upper() == "N":
                new_messages.append(ToolMessage(content="User denied Python execution.", tool_call_id=tool_call["id"]))
                continue

            elif approval.upper() == "A":
                python_policy = "allow"

        tool_response = execute_tool(tool_call)
        new_messages.append(tool_response)

    return {
        "messages": new_messages,
        "python_policy": python_policy,
        "pending_tool_calls": [],
    }