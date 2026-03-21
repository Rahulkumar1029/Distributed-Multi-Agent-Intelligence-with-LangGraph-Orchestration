import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_mcp_adapters.client import MultiServerMCPClient
from bot1_LG_MCP.resources.tools import internet_search
from bot1_LG_MCP.resources.llms import bot2_llm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import logging
import asyncio

client = MultiServerMCPClient({
    "expense-tracker": {
        "transport": "stdio",
        "command": "uv",
        "args": [
            "run",
            "--directory",
            "C:/Users/rahul/Desktop/mcp_server/expense-tracker-mcp-server",
            "main.py"
        ]
    }
})

class AgentState(MessagesState):
    pass

async def create_graph2():

    try:
        mcp_tools = await client.get_tools()
        tools = mcp_tools + [internet_search]
    except Exception as e:
        print(f"[create_graph2] MCP server unavailable, using internet_search only. Error: {e}")
        tools = [internet_search]

    llm_google = bot2_llm()
    llm_with_tools = llm_google.bind_tools(tools)

    async def llm_node(state: AgentState):
        messages = state["messages"]

        # 🛡️ BULLETPROOFING: Clean orphans
        cleaned_messages = []
        from langchain_core.messages import AIMessage, ToolMessage
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                if i + 1 < len(messages) and isinstance(messages[i+1], ToolMessage):
                    cleaned_messages.append(msg)
                else:
                    # Drop the broken tool call so it doesn't crash Gemini
                    cleaned_messages.append(AIMessage(content=msg.content or "Tool execution interrupted."))
            else:
                cleaned_messages.append(msg)

        response = await llm_with_tools.ainvoke(cleaned_messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)

    builder.add_node("llm_node", llm_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))

    builder.add_edge(START, "llm_node")
    builder.add_conditional_edges("llm_node", tools_condition)
    builder.add_edge("tools", "llm_node")

    checkpointer = InMemorySaver()

    graph = builder.compile(checkpointer=checkpointer)

    return graph
