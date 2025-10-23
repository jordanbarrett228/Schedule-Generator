from typing import Optional
import datetime as dt
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime
from sqlmodel import Field, SQLModel
from .dbbase import DBBase

class EmployeeBase(DBBase):
    name: str
    active: bool = True  # treat as "include in generation" toggle for now

    # Hard constraints (per-employee caps)
    min_hours_week: float = 20  # HR requirement: minimum 20 hours per employee
    max_hours_week: float = 40
    min_shift_hours: float = 4
    max_shift_hours: float = 7

    # Clopen protection
    no_clopen: bool = False
    clopen_next_day_not_before: Optional[dt.time] = Field(default=dt.time(9, 0), sa_column=Column(SATime, nullable=True))

    # Soft preferences
    preferred_hours: Optional[float] = 25
    prefer_opening: bool = True
    prefer_mid: bool = True
    prefer_closing: bool = True
    max_consecutive_days: Optional[int] = None
    allow_split_shifts: bool = False

    # Soft: target # of days off in a week
    target_days_off: Optional[int] = 2  # 0..7

    position: str = Field(default="Guest Services Specialist")

class Employee(EmployeeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int

class EmployeeUpdate(DBBase):
    name: Optional[str] = None
    active: Optional[bool] = None
    min_hours_week: Optional[float] = None
    max_hours_week: Optional[float] = None
    min_shift_hours: Optional[float] = None
    max_shift_hours: Optional[float] = None
    preferred_hours: Optional[float] = None
    prefer_opening: Optional[bool] = None
    prefer_mid: Optional[bool] = None
    prefer_closing: Optional[bool] = None
    max_consecutive_days: Optional[int] = None
    allow_split_shifts: Optional[bool] = None
    no_clopen: Optional[bool] = None
    clopen_next_day_not_before: Optional[dt.time] = Field(default=None, sa_column=Column(SATime, nullable=True))
    target_days_off: Optional[int] = None
    position: Optional[str] = None
