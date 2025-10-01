from __future__ import annotations

from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Date as SADate, Time as SATime

class TimeOffBase(SQLModel):
    employee_id: int = Field(foreign_key="employee.id")
    date: dt.date = Field(sa_column=Column(SADate))
    all_day: bool = True
    start_time: Optional[dt.time] = Field(default=None, sa_column=Column(SATime, nullable=True))
    end_time: Optional[dt.time] = Field(default=None, sa_column=Column(SATime, nullable=True))
    reason: Optional[str] = None

class TimeOff(TimeOffBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class TimeOffCreate(TimeOffBase):
    pass

class TimeOffRead(TimeOffBase):
    id: int
