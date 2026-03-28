"""Main agent loop and state management."""
from typing import Annotated, Optional
from langchain_openai import ChatOpenAI
import os
import uuid
from pydantic import BaseModel
from langchain_core.messages import AnyMessage, HumanMessage
import operator
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from .tools import create_tools
from .sandbox import close_session_sandbox

class AgentState(BaseModel):
    """State for the agent."""
    messages: Annotated[list[AnyMessage], operator.add]


class GraphAgent:
    """Graph-based agent with tools."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the graph agent with LLM and tools."""
        self.session_id = session_id or str(uuid.uuid4())
        self.llm = ChatOpenAI(
            model="openai/gpt-5-nano",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        self.tools = create_tools(self.session_id)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.agent = self._build_graph()

    def close(self):
        """Release resources tied to this session."""
        close_session_sandbox(self.session_id)

    def _build_graph(self):
        """Build the agent graph."""
        def agent_node(state: AgentState):
            response = self.llm_with_tools.invoke(state.messages)
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
    
    def run(self, user_input: str) -> str:
        """Run the agent and return the final response."""
        result = self.agent.invoke({
            'messages': [HumanMessage(content=user_input)]
        })
        return result

    def stream(self, user_input: str):
        """Stream responses from the agent."""
        for chunk in self.agent.stream(
            AgentState(
                messages=[HumanMessage(content=user_input)]
            ),
            stream_mode="updates"
        ):
            yield(chunk)