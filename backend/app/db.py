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

def set_data_directory(data_dir: str):
    """
    Change the database path to a custom directory (for Electron app)
    Must be called before init_db()
    """
    global settings, DATABASE_URL, engine
    settings.db_path = str(Path(data_dir) / "schedule.db")
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{settings.db_path}"
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

def init_db() -> None:
    from .models.dbbase import schedulemetadata
    from .models.settings import GlobalSettings, BusinessHours

    schedulemetadata.create_all(engine)

    # Initialize default business hours for single-user mode
    with Session(engine) as session:
        # Check if business hours exist
        existing_hours = session.exec(select(BusinessHours)).first()
        if not existing_hours:
            # Create default business hours
            defaults = {
                0: (time(4,45), time(21,15)),  # Mon
                1: (time(4,45), time(21,15)),  # Tue
                2: (time(4,45), time(21,15)),  # Wed
                3: (time(4,45), time(21,15)),  # Thu
                4: (time(4,45), time(21,15)),  # Fri
                5: (time(5,45), time(21,15)),  # Sat
                6: (time(11,45), time(18,15)), # Sun
            }
            for weekday, (open_time, close_time) in defaults.items():
                session.add(BusinessHours(weekday=weekday, open_time=open_time, close_time=close_time))
            session.commit()

        # Check if global settings exist
        existing_settings = session.exec(select(GlobalSettings)).first()
        if not existing_settings:
            session.add(GlobalSettings())
            session.commit()

# FastAPI dependency
def get_session():
    with Session(engine) as session:
        yield session