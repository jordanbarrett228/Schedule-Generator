from __future__ import annotations

from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime, Date as SADate

class GlobalSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    min_staff_default: int = Field(default=2)

class BusinessHoursBase(SQLModel):
    weekday: int  # 0=Mon..6=Sun
    open_time: dt.time = Field(sa_column=Column(SATime))
    close_time: dt.time = Field(sa_column=Column(SATime))

class BusinessHours(BusinessHoursBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class BusinessHoursCreate(BusinessHoursBase):
    pass

class BusinessHoursRead(BusinessHoursBase):
    id: int

class CoveragePeakBase(SQLModel):
    # Provide EITHER a specific date OR a weekday (0=Mon..6=Sun)
    date: Optional[dt.date] = Field(default=None, sa_column=Column(SADate, nullable=True))
    weekday: Optional[int] = Field(default=None)
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))
    min_staff: int = Field(default=3)

class CoveragePeak(CoveragePeakBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class CoveragePeakCreate(CoveragePeakBase):
    pass

class CoveragePeakRead(CoveragePeakBase):
    id: int