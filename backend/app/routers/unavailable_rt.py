from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import time as dt_time
from sqlmodel import Session, select

from app.db import get_session
from app.models.unavailable import UnavailableBlock

router = APIRouter(prefix="/api/unavailable", tags=["unavailable"])

WEEKDAYS = set(range(0, 7))

class UnavailableUpdate(BaseModel):
    weekday: int
    start_time: dt_time
    end_time: dt_time

    @field_validator("weekday")
    @classmethod
    def _weekday(cls, v: int) -> int:
        if v not in WEEKDAYS:
            raise ValueError("weekday must be 0..6 (Mon=0 .. Sun=6)")
        return v

    @field_validator("end_time")
    @classmethod
    def _end_after_start(cls, end: dt_time, info):
        start: Optional[dt_time] = info.data.get("start_time")
        if start is not None and end <= start:
            raise ValueError("end_time must be after start_time")
        return end


@router.put("/{unavail_id}")
def update_unavailable(
    unavail_id: int,
    payload: UnavailableUpdate,
    session: Session = Depends(get_session),
):
    u = session.get(UnavailableBlock, unavail_id)
    if not u:
        raise HTTPException(status_code=404, detail="Unavailable not found")

    # Update fields
    u.weekday = payload.weekday
    u.start_time = payload.start_time
    u.end_time = payload.end_time

    session.add(u)
    session.commit()
    session.refresh(u)
    return {
        "id": u.id,
        "employee_id": u.employee_id,
        "weekday": u.weekday,
        # FastAPI will JSON-serialize dt.time as "HH:MM:SS"; if you want "HH:MM",
        # slice below. Otherwise, return the time objects directly.
        "start_time": u.start_time.strftime("%H:%M"),
        "end_time": u.end_time.strftime("%H:%M"),
    }
