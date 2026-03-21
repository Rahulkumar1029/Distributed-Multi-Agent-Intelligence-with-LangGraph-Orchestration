import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_huggingface import HuggingFaceEmbeddings
from bot1_LG_MCP.resources.llms import bot3_llm
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

PERSIST_DIR = "chroma_db"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

llm = bot3_llm()

@tool
def retrieve(query: str) -> str:
    """Retrieve relevant documents from vectorstore."""
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    return f"Relevant context:\n{context}"


class AgentState(MessagesState):
    pass

async def build_graph():

    tools = [retrieve]
    llm_with_tools = llm.bind_tools(tools)

    # -------- LLM NODE --------
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
                    cleaned_messages.append(AIMessage(content=msg.content or "Tool execution interrupted."))
            else:
                cleaned_messages.append(msg)

        response = await llm_with_tools.ainvoke(cleaned_messages)

        return {"messages": [response]}

    # -------- TOOL NODE --------
    tool_node = ToolNode(tools, handle_tool_errors=True)

    # -------- GRAPH --------
    builder = StateGraph(AgentState)

    builder.add_node("llm", llm_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "llm")

    builder.add_conditional_edges(
        "llm",
        tools_condition
    )

    builder.add_edge("tools", "llm")
    checkpointer=InMemorySaver()

    graph = builder.compile(checkpointer=checkpointer)

    return graph

