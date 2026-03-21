from sqlalchemy import Column, Integer, String, Text , TIMESTAMP,ForeignKey
from Backend.DB.db import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import LONGTEXT

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP,server_default=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    bot_id = Column(String(50), default="bot1", index=True)
    thread_id = Column(String(255), unique=True, index=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(TIMESTAMP, server_default=func.now())

class Chat_record(Base):
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    bot_id = Column(String(50), default="bot1", index=True)
    thread_id = Column(String(255), unique=True, index=True)
    message = Column(LONGTEXT)