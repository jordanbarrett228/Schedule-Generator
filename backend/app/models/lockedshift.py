from __future__ import annotations

from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Date as SADate, Time as SATime

class LockedShiftBase(SQLModel):
    employee_id: int = Field(foreign_key="employee.id")
    date: dt.date = Field(sa_column=Column(SADate))
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))
    note: Optional[str] = None

class LockedShift(LockedShiftBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class LockedShiftCreate(LockedShiftBase):
    pass

class LockedShiftRead(LockedShiftBase):
    id: int
