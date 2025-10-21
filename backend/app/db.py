import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select
from pydantic_settings import BaseSettings
from datetime import time

class Settings(BaseSettings):
    db_path: str = "./data/schedule.db"
    jwt_secret_key: str | None = None
    jwt_algorithm: str | None = None

    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"

settings = Settings()
Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{settings.db_path}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

def init_db() -> None:
    from .models.dbbase import schedulemetadata
    schedulemetadata.create_all(engine)

# FastAPI dependency
def get_session():
    with Session(engine) as session:
        yield session