import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "./data/schedule.db"
    class Config:
        env_file = ".env"
        env_prefix = ""


settings = Settings()


# Ensure data dir exists
Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)


# SQLite URL must be a filesystem path
DATABASE_URL = f"sqlite:///{settings.db_path}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    # Import models here so SQLModel sees them before create_all
    from .models.employee import Employee # noqa: F401
    SQLModel.metadata.create_all(engine)


# Dependency for FastAPI routes


def get_session():
    with Session(engine) as session:
        yield session