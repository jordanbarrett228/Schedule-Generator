from sqlmodel import SQLModel, create_engine
from pathlib import Path

DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'database.db'}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
