# add interrupt, incremental messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage 
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from typing import Any, TypedDict, Annotated

from single_agent.agent import llm_with_python
from tools.py_tool import execute_python_code
SYSTEM_PROMPT = 'You have a tool available to you, named execute_python_code, which provides you with a python envieronment, which has a df loaded in it, with the name `df`.'

memory = InMemorySaver()

# Tool Registary
ALL_TOOLS = [execute_python_code]
TOOLS = {tool.name:tool for tool in ALL_TOOLS}

# State 
class AgentState(TypedDict): # state schema
    messages: Annotated[list[BaseMessage] , add_messages]
    python_policy: str
    pending_tool_calls: list

# Util functions
def execute_tool(tool_call:dict[str,Any]) -> ToolMessage:
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

# Nodes

def planner(agent_state:AgentState) -> AgentState:
    ''' Think and append AIMessage '''
    
    response:AIMessage = llm_with_python.invoke(agent_state['messages'])
    if not response.tool_calls: print(f"AI: {response.content}")

    return {'messages':[response], 'pending_tool_calls': response.tool_calls}

def tool_executor(agent_state: AgentState) -> AgentState:
    python_policy = agent_state['python_policy']
    decisions = {}  # tool_call id -> approved?

    # Phase 1: approvals only, with no side effects
    for tool_call in agent_state["pending_tool_calls"]:
        if tool_call['name'] == 'execute_python_code' and python_policy == 'ask':
            approval = interrupt({"type": "python_approval",
                                  "code": tool_call["args"]["code"]}).upper()
            if approval == 'A':
                python_policy = 'allow'
            decisions[tool_call['id']] = approval != 'N'
        else:
            decisions[tool_call['id']] = True

    # Phase 2: execution, reached only once, after all interrupts are answered
    new_messages = []
    for tool_call in agent_state["pending_tool_calls"]:
        if decisions[tool_call['id']]:
            new_messages.append(execute_tool(tool_call))
        else:
            new_messages.append(ToolMessage(
                content="User denied Python execution.",
                tool_call_id=tool_call["id"]))

    return {'messages': new_messages,
            'python_policy': python_policy,
            'pending_tool_calls': []}

def should_continue(agent_state: AgentState) -> str:

    return "tool_executor" if agent_state["pending_tool_calls"] else END

builder = StateGraph(AgentState)
builder.add_node('planner',planner)
builder.add_node('tool_executor',tool_executor)

builder.add_edge(START, 'planner')
builder.add_edge('tool_executor', 'planner')

builder.add_conditional_edges('planner', should_continue, {'tool_executor':'tool_executor', END:END})

graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "demo"}}


initialized = False
while True:
    text = input("Human: ")
    if text.lower() in ("quit", "exit", "bye"):
        break

    if not initialized:
        graph_input = {
            "messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=text)],
            "python_policy": "ask",
            "pending_tool_calls": [],
        }
        initialized = True
    else:
        graph_input = {"messages": [HumanMessage(content=text)]}

    result = graph.invoke(graph_input, config=config)

    # Handle human approval interrupts
    while "__interrupt__" in result:

        interrupt_obj = result["__interrupt__"][0]

        payload = interrupt_obj.value

        print("\nLLM wants to execute:\n")
        print(payload["code"])

        approval = input("\nApprove (Y/N/A): ").strip().upper()

        while approval not in ("Y", "N", "A"):
            approval = input("Approve (Y/N/A): ").strip().upper()

        result = graph.invoke(
            Command(resume=approval),
            config=config,
        )

    messages = result["messages"]

    if isinstance(messages[-1], AIMessage):
        print(f"AI: {messages[-1].content}")

state = graph.get_state(config)
show_flow(state.values)