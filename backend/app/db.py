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
    from .models.employee import Employee  # noqa: F401
    from .models.unavailable import UnavailableBlock  # noqa: F401
    from .models.timeoff import TimeOff  # noqa: F401
    from .models.lockedshift import LockedShift  # noqa: F401
    from .models.settings import GlobalSettings, CoveragePeak, BusinessHours  # noqa: F401

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Ensure one GlobalSettings row
        gs = session.exec(select(GlobalSettings)).first()
        if not gs:
            gs = GlobalSettings(min_staff_default=2)
            session.add(gs)
            session.commit()
        # Seed BusinessHours for 7 days if missing
        have = session.exec(select(BusinessHours)).all()
        if not have:
            # New defaults:
            # Mon-Fri: 04:45 - 21:15
            # Sat: 05:45 - 21:15
            # Sun: 11:45 - 18:15
            defaults = {
                0: (time(4,45), time(21,15)),
                1: (time(4,45), time(21,15)),
                2: (time(4,45), time(21,15)),
                3: (time(4,45), time(21,15)),
                4: (time(4,45), time(21,15)),
                5: (time(5,45), time(21,15)),  # Sat
                6: (time(11,45), time(18,15)),  # Sun
            }
            for wd, (op, cl) in defaults.items():
                session.add(BusinessHours(weekday=wd, open_time=op, close_time=cl))
            session.commit()


# FastAPI dependency
def get_session():
    with Session(engine) as session:
        yield session