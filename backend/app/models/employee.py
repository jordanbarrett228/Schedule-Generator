from typing import Optional
from sqlmodel import Field, SQLModel

class EmployeeBase(SQLModel):
    name: str
    active: bool = True  # treat as "include in generation" toggle for now
    # Hard constraints (per-employee caps)
    min_hours_week: float = 20
    max_hours_week: float = 40
    min_shift_hours: float = 4
    max_shift_hours: float = 8
    # Soft preferences
    preferred_hours: Optional[float] = None
    prefer_opening: bool = True
    prefer_mid: bool = True
    prefer_closing: bool = True
    max_consecutive_days: Optional[int] = None
    allow_split_shifts: bool = False

class Employee(EmployeeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int

class EmployeeUpdate(SQLModel):
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