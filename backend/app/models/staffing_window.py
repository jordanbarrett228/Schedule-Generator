from __future__ import annotations
from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime

class StaffingWindowBase(SQLModel):
    weekday: int  # 0=Sun .. 6=Sat
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))
    # Minimum staff target (heavily weighted soft constraint - solver will strongly try to meet this)
    min_staff: Optional[int] = None
    # Maximum staff cap (hard constraint - solver cannot exceed this)
    max_staff: Optional[int] = None
    # If true, prefer fewer/longer shifts for this day (stronger start penalty)
    prefer_full_length: bool = False

class StaffingWindow(StaffingWindowBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class StaffingWindowCreate(StaffingWindowBase):
    pass

class StaffingWindowRead(StaffingWindowBase):
    id: int
