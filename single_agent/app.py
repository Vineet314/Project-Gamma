from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage 
from typing import Any

from single_agent.agent import llm_with_python
from tools.py_tool import execute_python_code
SYSTEM_PROMPT = None

# Tool Registary
ALL_TOOLS = [execute_python_code]
TOOLS = {tool.name:tool for tool in ALL_TOOLS}

# State 
agent_state:dict[str,Any] = {}
agent_state['messages'] = [SystemMessage(content=SYSTEM_PROMPT)]
agent_state['python_policy'] = 'ask' # default to ask. Other option: `allow`
agent_state['pending_tool_calls'] = []
agent_state['next_node'] = 'human_input'

# Util functions
def execute_tool(tool_call:dict[str, Any]) -> ToolMessage:
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

def show_flow(agent_state:dict[str, Any]) -> None:
    print()
    for msg in agent_state['messages']:
        if isinstance(msg, SystemMessage): continue
        print(type(msg).__name__)
        if isinstance(msg, AIMessage): 
            for call in msg.tool_calls:
                print(call['name'], call['args'])
        print(msg.content)
        print("-" * 80)

# Nodes
def human_input(agent_state:dict[str, Any]) -> dict[str, Any]:
    ''' Adds a human message '''
    human_input = HumanMessage(content=input('Human: '))
    agent_state['messages'].append(human_input)
    agent_state['next_node'] = 'planner' if human_input.content.lower() not in ('quit','exit','bye') else 'exit'
    return agent_state

def planner(agent_state:dict[str, Any]) -> dict[str, Any]:
    ''' Think and append AIMessage '''
    
    response:AIMessage = llm_with_python.invoke(agent_state['messages'])
    agent_state['messages'].append(response)
    agent_state['pending_tool_calls'] = response.tool_calls
    agent_state['next_node'] = 'tool_executor' if response.tool_calls else 'human_input'
    if not response.tool_calls: print(f"AI: {response.content}")
    return agent_state

def tool_executor(agent_state:dict[str, Any]) -> dict[str, Any]:
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
    agent_state['next_node'] = 'planner'
    return agent_state

def exit():
    ''' A special exit node '''
    import sys; sys.exit('\n\nThank you for using this agent')

NODES = {"human_input": human_input, "planner": planner, "tool_executor": tool_executor}

while agent_state['next_node'] != 'exit':
    try:
        node = NODES[agent_state['next_node']]
        agent_state = node(agent_state)
    except KeyboardInterrupt:
        exit() # call the exit node, won't print agent flow

print('\n-------------------------------------------------\n')
show_flow(agent_state)