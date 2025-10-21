from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime
from datetime import time as dt_time
from .dbbase import DBBase

WEEKDAYS = set(range(0, 7))

class LockedShiftBase(DBBase):
    employee_id: int = Field(foreign_key="employee.id")
    weekday: int  # 0=Mon..6=Sun
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))
    note: Optional[str] = None
    
class LockedShift(LockedShiftBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class LockedShiftCreate(LockedShiftBase):
    pass

class LockedShiftRead(LockedShiftBase):
    id: int

class LockedShiftUpdate(BaseModel):
    weekday: int
    start_time: dt_time
    end_time: dt_time
    note: Optional[str] = None

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

