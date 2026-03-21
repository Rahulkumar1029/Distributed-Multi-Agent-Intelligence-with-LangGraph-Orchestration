import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from Backend.routers.endpoints import router1 as auth_router
from Backend.routers.endpoints import router2 
from Backend.routers.endpoints import bot
from fastapi.middleware.cors import CORSMiddleware
from bot1_LG_MCP.main import create_graph
from bot2_exp_tracker.main import create_graph2
from bot3_rag.rag_engine import build_graph
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from bot4_A2A.main import create_main_graph,MultiBotAgent

CONN_STRING = "postgresql://Agent:asdfghjkl1234@localhost:5432/AgentDB?sslmode=disable"

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with AsyncConnectionPool(
        conninfo=CONN_STRING,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    ) as pool:

        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()

        graph = await create_graph(checkpointer)
        graph2 = await create_graph2()
        graph3=await build_graph()
        agent=MultiBotAgent(checkpointer)
        await agent.initialize_bots()
        graph4=await create_main_graph(agent)

        app.state.graph = graph
        app.state.graph2 = graph2
        app.state.graph3 = graph3
        app.state.graph4 = graph4

        yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router2)
app.include_router(bot)
