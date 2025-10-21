# backend/app/utils/user_defaults.py
from sqlmodel import Session, select
from datetime import time
from app.models.settings import GlobalSettings, BusinessHours
from app.db import engine

def ensure_user_settings(user_id: int):
    """Ensure a user has default GlobalSettings and BusinessHours records."""
    # 1️⃣ GlobalSettings
    with Session(engine) as session:
        gs = session.exec(select(GlobalSettings).where(GlobalSettings.user_id == user_id)).first()
        if not gs:
            gs = GlobalSettings(user_id=user_id)
            session.add(gs)
            session.commit()
            session.refresh(gs)

        # 2️⃣ BusinessHours defaults
        existing = session.exec(select(BusinessHours).where(BusinessHours.user_id == user_id)).all()
        if not existing:
            defaults = {
                0: (time(4,45), time(21,15)),  # Mon
                1: (time(4,45), time(21,15)),  # Tue
                2: (time(4,45), time(21,15)),  # Wed
                3: (time(4,45), time(21,15)),  # Thu
                4: (time(4,45), time(21,15)),  # Fri
                5: (time(5,45), time(21,15)),  # Sat
                6: (time(11,45), time(18,15)), # Sun
            }
            for wd, (op, cl) in defaults.items():
                session.add(BusinessHours(user_id=user_id, weekday=wd, open_time=op, close_time=cl))
            session.commit()
