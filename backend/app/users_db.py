# backend/app/users_db.py
from sqlmodel import create_engine, SQLModel, Session
from pathlib import Path

_USERS_DB_PATH = Path(__file__).resolve().parents[1] / "backend" / "data" / "users.db"
_USERS_DB_URL = f"sqlite:///{_USERS_DB_PATH}"

users_engine = create_engine(_USERS_DB_URL, echo=False)

def create_users_db_and_tables():
    from .models.user import User
    SQLModel.metadata.create_all(users_engine)

def get_users_session():
    return Session(users_engine)