from langchain_openai import ChatOpenAI
# from tools.csv_tools import all_tools
from tools.py_tool import execute_python_code

llm = ChatOpenAI(model="gpt-5.4-nano")
# llm_with_tools = llm.bind_tools(all_tools)
llm_with_python = llm.bind_tools([execute_python_code])