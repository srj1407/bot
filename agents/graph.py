import os
from typing_extensions import TypedDict
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage
import json
from typing import Annotated, TypedDict, Optional
from langchain_core.messages import AnyMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class graphAgent():
    def __init__(self, session_id: Optional[str] = None):
        self.model="stepfun/step-3.5-flash:free"
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        self.tools = self._load_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.agent = self._build_graph()
        self.stream_agent = self._build_stream_graph()
        self.session_id=session_id

    def _load_tools(self):
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
        search = DuckDuckGoSearchRun()
        tools = [calculator, search]
        return tools

    def _build_graph(self):
        def agent_node(state: MessagesState):
            response = self.llm_with_tools.invoke(state['messages'])
            return {'messages': [response]}

        graph = StateGraph(MessagesState)
        graph.add_node('tools', ToolNode(self.tools))
        graph.add_node('agent', agent_node)
        graph.set_entry_point('agent')
        graph.add_conditional_edges(
            'agent',
            tools_condition
        )
        graph.add_edge('tools', 'agent')
        app = graph.compile()
        return app
    
    def _build_stream_graph(self):
        async def agent_node(state: AgentState):
            response = await self.llm_with_tools.ainvoke(state['messages'])
            return {'messages': [response]}

        graph = StateGraph(AgentState)
        graph.add_node('tools', ToolNode(self.tools))
        graph.add_node('agent', agent_node)
        graph.set_entry_point('agent')
        graph.add_conditional_edges(
            'agent',
            tools_condition
        )
        graph.add_edge('tools', 'agent')
        app = graph.compile()
        return app
    
    async def run(self, user_input: str) -> str:
        result = await self.agent.ainvoke({
            'messages': [HumanMessage(content=user_input)]
        })
        return {
            'result': result['messages'][-1].content,
            'model': self.model
        }
    
    async def stream_run(self, user_input: str):
        input={
            'messages': [HumanMessage(content=user_input)]
        }
        async for event in self.stream_agent.astream_events(input, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                # if content:
                #     yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                if content:
                    yield content
        