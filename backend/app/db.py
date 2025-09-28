import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select
from pydantic_settings import BaseSettings
from datetime import time

class Settings(BaseSettings):
    db_path: str = "./data/schedule.db"
    class Config:
        env_file = ".env"
        env_prefix = ""

settings = Settings()
Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{settings.db_path}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

def init_db() -> None:
    # Import models so SQLModel sees them
    from .models.employee import Employee  # noqa: F401
    from .models.unavailable import UnavailableBlock  # noqa: F401
    from .models.timeoff import TimeOff  # noqa: F401
    from .models.lockedshift import LockedShift  # noqa: F401
    from .models.settings import GlobalSettings, CoveragePeak  # noqa: F401

    SQLModel.metadata.create_all(engine)

    # Ensure one GlobalSettings row
    with Session(engine) as session:
        existing = session.exec(select(GlobalSettings)).first()
        if not existing:
            gs = GlobalSettings(min_staff_default=2, business_open=time(8,0), business_close=time(21,0))
            session.add(gs)
            session.commit()


# FastAPI dependency
def get_session():
    with Session(engine) as session:
        yield session