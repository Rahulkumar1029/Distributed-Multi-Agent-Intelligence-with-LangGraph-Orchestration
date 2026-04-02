from langgraph.graph import StateGraph,START,END,MessagesState
from bot1_LG_MCP.resources.llms import bot1_llm
from langgraph.prebuilt import ToolNode,tools_condition
from bot1_LG_MCP.resources.tools import get_all_tools
from langchain_core.messages import BaseMessage,AIMessage,HumanMessage,ToolMessage
import os
import logging
from typing import List
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.generativeai").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    thread_id: str

class AgentState(MessagesState):
     pass


async def create_graph(checkpointer):

    tools = await get_all_tools()
    llm_google = bot1_llm()
    llm_with_tools = llm_google.bind_tools(tools)

    async def llm_node(state: AgentState):
        messages = state["messages"]

        system_message = {
            "role": "system",
            "content": "for any code of station or airport use internet search"
        }

        cleaned_messages = []
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                if i + 1 < len(messages) and isinstance(messages[i+1], ToolMessage):
                    cleaned_messages.append(msg)
                else:
                    cleaned_messages.append(AIMessage(content=msg.content or "Tool execution interrupted."))
            else:
                cleaned_messages.append(msg)

        cleaned_messages.append(HumanMessage(content="for any code of station or airport use internet search"))
        response = await llm_with_tools.ainvoke([system_message] + cleaned_messages)
        if response is None:
            response = AIMessage(content="Sorry, something went wrong.")

        return {"messages": [response]}

    builder = StateGraph(AgentState)

    builder.add_node("llm_node", llm_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))

    builder.add_edge(START, "llm_node")
    builder.add_conditional_edges("llm_node", tools_condition)
    builder.add_edge("tools", "llm_node")

    graph = builder.compile(checkpointer=checkpointer)
    return graph

