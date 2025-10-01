from __future__ import annotations
from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime

class StaffingWindowBase(SQLModel):
    weekday: int  # 0=Mon .. 6=Sun
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))
    # Soft preferred minimum coverage during this window
    min_staff: Optional[int] = None
    # Hard cap during this window (<=)
    max_staff: Optional[int] = None
    # If true, prefer fewer/longer shifts for this day (stronger start penalty)
    prefer_full_length: bool = False

class StaffingWindow(StaffingWindowBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class StaffingWindowCreate(StaffingWindowBase):
    pass

class StaffingWindowRead(StaffingWindowBase):
    id: int
