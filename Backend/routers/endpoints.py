from fastapi import APIRouter, UploadFile,File
from Backend.DB.db import SessionLocal, Base, engine
from Backend.DB.models import User,ChatSession
from Backend.schemas.schemas import UserCreate,ChatInput,ChatInput2
from Backend.security.basic_auth import hash_password,get_current_user,get_optional_user,get_optional_user_from_request
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from fastapi import Request, Depends,APIRouter
from datetime import datetime
import traceback
from fastapi.responses import StreamingResponse
import asyncio
from langchain_core.messages import AIMessageChunk, ToolMessage
import json


router1 = APIRouter(prefix="/auth")
Base.metadata.create_all(bind=engine)
@router1.post("/signup")
def signup(user: UserCreate):
    db = SessionLocal()
    hashed = hash_password(user.password)
    new_user = User(username=user.username, password=hashed)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}


@router1.get("/login")
def login(current_user: User = Depends(get_current_user)):
    return {
        "message": "Login successful",
        "user_id": current_user.id,
        "username": current_user.username
    }


router2=APIRouter()
@router2.post("/create_chat")
def create_chat(bot_id: str, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    thread_id=f"{current_user.username}_{bot_id}_{datetime.now().strftime('%H:%M:%S')}"
    title=f"Chat {datetime.now().strftime('%d %b %H:%M')}"
    new_chat=ChatSession(user_id=current_user.username,thread_id=thread_id,title=title,bot_id=bot_id)
    db.add(new_chat)
    db.commit()
    return {
        "message": "Chat created successfully",
        "chat_id": new_chat.id,
        "thread_id": new_chat.thread_id,
        "title": new_chat.title,
        "bot_id": new_chat.bot_id
    }


@router2.get("/get_chats")
def get_chats(bot_id: str, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    chats = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == current_user.username,
            ChatSession.bot_id == bot_id
        )
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "thread_id": c.thread_id,
            "title": c.title,
            "bot_id": c.bot_id
        }
        for c in chats
    ]


bot=APIRouter(prefix="/chat")
@bot.post("/bot1",response_class=StreamingResponse)
async def chat_bot1(body: ChatInput, request: Request):

    graph = request.app.state.graph

    async def sse_stream():
        config = {"configurable": {"thread_id": body.thread_id}}
        final_text = ""

        from langchain_core.tracers.context import tracing_v2_enabled
        try:
            # ✅ Industry Standard: stream_mode="messages" yields (chunk, metadata)
            with tracing_v2_enabled(project_name="Bot 1 (Travel)"):
                async for msg_chunk, metadata in graph.astream(
                    {"messages": [HumanMessage(content=body.text)]},
                    config,
                    stream_mode="messages"
                ):
                    # 1. Stream Assistant Tokens
                    if isinstance(msg_chunk, AIMessageChunk):
                        # Some models return string, some return list of blocks
                        token = ""
                        if isinstance(msg_chunk.content, str):
                            token = msg_chunk.content
                        elif isinstance(msg_chunk.content, list):
                            token = "".join(
                                block.get("text", "") 
                                for block in msg_chunk.content 
                                if isinstance(block, dict) and block.get("type") == "text"
                            )

                        if token:
                            final_text += token
                            payload = {
                                "type": "token",
                                "content": token,
                                "is_delta": True  # Flag for our frontend parser
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                        # 2. Stream Tool Calls
                        if getattr(msg_chunk, "tool_calls", None):
                            payload = {
                                "type": "tool_call",
                                "tools": msg_chunk.tool_calls
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                    # 3. Stream Tool Results
                    elif isinstance(msg_chunk, ToolMessage):
                        payload = {
                            "type": "tool_result",
                            "content": str(msg_chunk.content)
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                # 4. End of generation confirmation
                payload = {
                    "type": "final",
                    "content": final_text.strip()
                }
                yield f"data: {json.dumps(payload)}\n\n"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_payload = {
                "type": "error",
                "error": str(e),
                "trace": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
        }
    )

@bot.post("/bot2",response_class=StreamingResponse)
async def chat_bot2(body: ChatInput2, request: Request):

    graph = request.app.state.graph2

    async def sse_stream():
        config = {"configurable": {"thread_id": body.thread_id}}
        final_text = ""

        from langchain_core.tracers.context import tracing_v2_enabled
        try:
            # ✅ Industry Standard: stream_mode="messages" yields (chunk, metadata)
            with tracing_v2_enabled(project_name="Bot 2 (Expense)"):
                async for msg_chunk, metadata in graph.astream(
                    {"messages": [HumanMessage(content=body.text)]},
                    config,
                    stream_mode="messages"
                ):
                    # 1. Stream Assistant Tokens
                    if isinstance(msg_chunk, AIMessageChunk):
                        # Some models return string, some return list of blocks
                        token = ""
                        if isinstance(msg_chunk.content, str):
                            token = msg_chunk.content
                        elif isinstance(msg_chunk.content, list):
                            token = "".join(
                                block.get("text", "") 
                                for block in msg_chunk.content 
                                if isinstance(block, dict) and block.get("type") == "text"
                            )

                        if token:
                            final_text += token
                            payload = {
                                "type": "token",
                                "content": token,
                                "is_delta": True  # Flag for our frontend parser
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                        # 2. Stream Tool Calls
                        if getattr(msg_chunk, "tool_calls", None):
                            payload = {
                                "type": "tool_call",
                                "tools": msg_chunk.tool_calls
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                    # 3. Stream Tool Results
                    elif isinstance(msg_chunk, ToolMessage):
                        payload = {
                            "type": "tool_result",
                            "content": str(msg_chunk.content)
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                # 4. End of generation confirmation
                payload = {
                    "type": "final",
                    "content": final_text.strip()
                }
                yield f"data: {json.dumps(payload)}\n\n"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_payload = {
                "type": "error",
                "error": str(e),
                "trace": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
        }
    )

@bot.post("/bot3", response_class=StreamingResponse)
async def chat_bot3(body: ChatInput2, request: Request):
    graph = request.app.state.graph3

    async def sse_stream():
        config = {"configurable": {"thread_id": body.thread_id}}
        final_text = ""

        from langchain_core.tracers.context import tracing_v2_enabled
        try:
            # ✅ Industry Standard: stream_mode="messages" yields (chunk, metadata)
            with tracing_v2_enabled(project_name="Bot 3 (RAG)"):
                async for msg_chunk, metadata in graph.astream(
                    {"messages": [HumanMessage(content=body.text)]},
                    config,
                    stream_mode="messages"
                ):
                    # 1. Stream Assistant Tokens
                    if isinstance(msg_chunk, AIMessageChunk):
                        token = ""
                        if isinstance(msg_chunk.content, str):
                            token = msg_chunk.content
                        elif isinstance(msg_chunk.content, list):
                            token = "".join(
                                block.get("text", "") 
                                for block in msg_chunk.content 
                                if isinstance(block, dict) and block.get("type") == "text"
                            )

                        if token:
                            final_text += token
                            payload = {
                                "type": "token",
                                "content": token,
                                "is_delta": True
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                    # 2. Stream Tool Calls
                    if getattr(msg_chunk, "tool_calls", None):
                        payload = {
                            "type": "tool_call",
                            "tools": msg_chunk.tool_calls
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                    # 3. Stream Tool Results
                    elif isinstance(msg_chunk, ToolMessage):
                        payload = {
                            "type": "tool_result",
                            "content": str(msg_chunk.content)
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                # 4. End of generation confirmation
                payload = {
                    "type": "final",
                    "content": final_text.strip()
                }
                yield f"data: {json.dumps(payload)}\n\n"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_payload = {
                "type": "error",
                "error": str(e),
                "trace": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
        }
    )
        

@bot.post("/bot4", response_class=StreamingResponse)
async def chat_bot4(body: ChatInput2, request: Request):
    graph = request.app.state.graph4

    async def sse_stream():
        config = {"configurable": {"thread_id": body.thread_id}}
        final_text = ""

        from langchain_core.tracers.context import tracing_v2_enabled
        try:
            # ✅ Industry Standard: stream_mode="messages" yields (chunk, metadata)
            with tracing_v2_enabled(project_name="Multi Bot Agent-Bot4"):
                async for msg_chunk, metadata in graph.astream(
                    {"messages": [HumanMessage(content=body.text)]},
                    config,
                    stream_mode="messages"
                ):
                    # 1. Stream Assistant Tokens
                    if isinstance(msg_chunk, AIMessageChunk):
                        token = ""
                        if isinstance(msg_chunk.content, str):
                            token = msg_chunk.content
                        elif isinstance(msg_chunk.content, list):
                            token = "".join(
                                block.get("text", "") 
                                for block in msg_chunk.content 
                                if isinstance(block, dict) and block.get("type") == "text"
                            )

                        if token:
                            final_text += token
                            payload = {
                                "type": "token",
                                "content": token,
                                "is_delta": True
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                    # 2. Stream Tool Calls
                    if getattr(msg_chunk, "tool_calls", None):
                        payload = {
                            "type": "tool_call",
                            "tools": msg_chunk.tool_calls
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                    # 3. Stream Tool Results
                    elif isinstance(msg_chunk, ToolMessage):
                        payload = {
                            "type": "tool_result",
                            "content": str(msg_chunk.content)
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                # 4. End of generation confirmation
                payload = {
                    "type": "final",
                    "content": final_text.strip()
                }
                yield f"data: {json.dumps(payload)}\n\n"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_payload = {
                "type": "error",
                "error": str(e),
                "trace": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
        }
    )

# @router2.post("/stt")
# async def speech_to_text(file: UploadFile = File(...)):
#     audio_bytes = await file.read()
#     text = await transcribe_audio(audio_bytes)
#     return text

# @router2.get("/chat/history/{thread_id}")
# def get_chat_history(thread_id: str, current_user = Depends(get_current_user)):
#     db = SessionLocal()

#     messages = (
#         db.query(ChatMessage)
#         .filter(
#             ChatMessage.user_id == current_user.id,
#             ChatMessage.thread_id == thread_id
#         )
#         .order_by(ChatMessage.id.asc())
#         .all()
#     )

#     return [
#         {"role": m.role, "content": m.content}
#         for m in messages
#     ]