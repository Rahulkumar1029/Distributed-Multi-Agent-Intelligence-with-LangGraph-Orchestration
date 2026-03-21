from typing_extensions import TypedDict
from typing import Annotated, Sequence
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import asyncio
from langgraph.prebuilt import create_react_agent
from bot1_LG_MCP.main import create_graph
from bot2_exp_tracker.main import create_graph2
from bot3_rag.rag_engine import build_graph
from bot1_LG_MCP.resources.tools import internet_search
from bot1_LG_MCP.resources.llms import bot4_llm
import os

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class MultiBotAgent:
    def __init__(self, checkpointer):
        self.checkpointer = checkpointer
        self.bot1_graph = None
        self.bot2_graph = None  
        self.bot3_graph = None

    async def initialize_bots(self):
        """✅ Async init ALL graphs with shared checkpointer."""
        self.bot1_graph = await create_graph(self.checkpointer)
        self.bot2_graph = await create_graph2()  # Pass checkpointer!
        self.bot3_graph = await build_graph()

    # ✅ FIXED: Proper async StructuredTool
    def get_bot1_tool(self):
        async def _bot1(query: str) -> str:
            """Travel: flights, trains."""
            config = {"configurable": {"thread_id": "bot1-thread"}}
            result = await self.bot1_graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}, 
                config
            )
            return result["messages"][-1].content

        return StructuredTool.from_function(
            coroutine=_bot1,
            name="travel_bot",
            description="use this tool for any information related to Flights, trains between two places.",
            args_schema=BotInput
        )

    def get_bot2_tool(self):
        async def _bot2(query: str) -> str:
            """Expense tracking."""
            config = {"configurable": {"thread_id": "bot2-thread"}}
            result = await self.bot2_graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}, 
                config
            )
            return result["messages"][-1].content

        return StructuredTool.from_function(
            coroutine=_bot2,
            name="expense_bot", 
            description="use this tool for any information related to add Expenses,sub Expenses,get Expenses,get summaries.",
            args_schema=BotInput
        )

    def get_bot3_tool(self):
        async def _bot3(query: str) -> str:
            """Solar machine maintenance."""
            config = {"configurable": {"thread_id": "bot3-thread"}}
            result = await self.bot3_graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}, 
                config
            )
            return result["messages"][-1].content

        return StructuredTool.from_function(
            coroutine=_bot3,
            name="maintenance_bot",
            description="use this tool for any information related to Solar machine info, stringer maintenance, etc.",
            args_schema=BotInput
        )

# ✅ Pydantic input schema
class BotInput(BaseModel):
    query: str = Field(..., description="User question")

async def create_main_graph(agent: MultiBotAgent):
    """✅ Fixed: create_react_agent (simplest!)."""
    tools = [
        agent.get_bot1_tool(),
        agent.get_bot2_tool(), 
        agent.get_bot3_tool(),
        internet_search
    ]
    
    llm_with_tools = bot4_llm().bind_tools(tools)
    async def llm_node(state: AgentState):
        messages = state["messages"]
        cleaned_messages = []
        from langchain_core.messages import AIMessage, ToolMessage
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                if i + 1 < len(messages) and isinstance(messages[i+1], ToolMessage):
                    cleaned_messages.append(msg)
                else:
                    cleaned_messages.append(AIMessage(content=msg.content or "Tool execution interrupted."))
            else:
                cleaned_messages.append(msg)
            tou
        response = await llm_with_tools.ainvoke(cleaned_messages)
        return {"messages": [response]}
    
    builder = StateGraph(AgentState)

    builder.add_node("llm_node", llm_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))

    builder.add_edge(START, "llm_node")
    builder.add_conditional_edges("llm_node", tools_condition)
    builder.add_edge("tools", "llm_node")

    checkpoint = InMemorySaver()

    graph = builder.compile(checkpointer=checkpoint)
   
    return graph