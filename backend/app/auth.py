# backend/app/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select, create_engine

from .models.user import User, UserRead

import os
from pathlib import Path

# Configuration: set these env vars in your environment (or use .env in dev)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-prod")  # change in production!
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# Users DB path (separate DB)
_USERS_DB_PATH = Path(__file__).resolve().parents[1] / ".." / "users.db"
# Normalize path string for create_engine
_USERS_DB_URL = f"sqlite:///{Path(_USERS_DB_PATH).resolve()}"

# SQLModel engine for users DB
users_engine = create_engine(_USERS_DB_URL, echo=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def create_users_db_and_tables():
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(users_engine)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.utcnow()
    if expires_delta:
        exp = now + expires_delta
    else:
        exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": exp.isoformat()}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise JWTError("Missing sub")
        return subject
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

# Dependency to get current user object from token
def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    username = decode_access_token(token)
    with Session(users_engine) as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return UserRead.from_orm(user)
