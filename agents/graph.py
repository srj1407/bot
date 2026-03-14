import os
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage


load_dotenv()

llm = ChatOpenAI(
    model="arcee-ai/trinity-large-preview:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

search = DuckDuckGoSearchRun()

@tool
def calculator(x: float, y: float, op: str) -> float:
    """Performs basic math. Operations: add, subtract, multiply, divide"""
    if op=='add':
        return x+y
    elif op=='subtract':
        return x-y
    elif op=='multiply':
        return x*y
    elif op=='divide':
        return x/y

tools = [calculator, search]

llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)

def agent_node(state: MessagesState):
    response = llm_with_tools.invoke(state['messages'])
    return {'messages': [response]}

graph = StateGraph(MessagesState)
graph.add_node('tools', tool_node)
graph.add_node('agent', agent_node)
graph.set_entry_point('agent')
graph.add_conditional_edges(
    'agent',
    tools_condition
)
graph.add_edge('tools', 'agent')

app = graph.compile()

q = input("Ask a question (or type quit): ").strip()
result = app.invoke({
    'messages': [HumanMessage(content=q)]
})
for message in result['messages']:
    print(message.content)