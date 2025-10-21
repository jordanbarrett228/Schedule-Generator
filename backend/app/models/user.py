# backend/app/models/user.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True): # type: ignore[call-arg, misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True

# For responses
class UserRead(SQLModel):
    id: int
    username: str
    is_active: bool

# For login body (not stored)
class UserLogin(SQLModel):
    username: str
    password: str