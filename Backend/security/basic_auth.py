from passlib.context import CryptContext
import secrets
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from Backend.DB.db import SessionLocal
from Backend.DB.models import User, ChatSession
import hashlib
from fastapi import Request
from base64 import b64decode


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    First apply sha256, then bcrypt hash the fixed-length sha256 hex.
    This avoids the bcrypt 72-byte limit error.
    """

    # pre-hash to sha256 (always 64 hex chars → 32 bytes)
    sha256_hex = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha256_hex)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify by sha256 + bcrypt verify.
    """

    sha256_hex = hashlib.sha256(plain.encode()).hexdigest()
    return pwd_context.verify(sha256_hex, hashed)


BASIC_AUTH_REALM = "Basic"

security = HTTPBasic()

def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    db = SessionLocal()
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": f"Basic realm={BASIC_AUTH_REALM}"},
        )
    return user

def get_optional_user(
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        return get_current_user(credentials)
    except:
        return None


def get_optional_user_from_request(request: Request):
    auth = request.headers.get("Authorization")

    if not auth:
        return None

    try:
        scheme, credentials = auth.split()

        if scheme.lower() != "basic":
            return None

        decoded = b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":")

        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()

        if user and verify_password(password, user.password):
            return user

        return None

    except:
        return None

def verify_chat(thread_id:str,user_id:str):
    db = SessionLocal()
    chat = db.query(ChatSession).filter(ChatSession.thread_id == thread_id, ChatSession.user_id == user_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect thread_id or user_id",
            headers={"WWW-Authenticate": f"Basic realm={BASIC_AUTH_REALM}"},
        )
    return chat