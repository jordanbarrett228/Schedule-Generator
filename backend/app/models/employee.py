from typing import Optional
from sqlmodel import Field, SQLModel


class EmployeeBase(SQLModel):
    name: str
    active: bool = True
    min_hours_week: float = 0
    max_hours_week: float = 40
    min_shift_hours: float = 3
    max_shift_hours: float = 8
    preferred_hours: Optional[float] = None
    preferred_time_of_day: Optional[str] = None # "opening"|"mid"|"closing"|None
    max_consecutive_days: Optional[int] = None


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
    preferred_time_of_day: Optional[str] = None
    max_consecutive_days: Optional[int] = None