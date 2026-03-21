from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class ChatInput(BaseModel):
    text: str
    thread_id:str
    user_id:str

class ChatInput2(BaseModel):
    text: str
    user_id: str
    thread_id: str