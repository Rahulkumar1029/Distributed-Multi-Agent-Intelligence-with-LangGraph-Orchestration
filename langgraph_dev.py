import asyncio
from bot1_LG_MCP.main import create_graph
from bot3_rag.rag_engine import build_graph

graph_bot1 = asyncio.run(create_graph(checkpointer=None))
graph_bot3 = asyncio.run(build_graph())