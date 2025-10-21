from __future__ import annotations

from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import Time as SATime

class UnavailableBlockBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    employee_id: int = Field(foreign_key="employee.id")
    weekday: int  # 0=Mon .. 6=Sun
    start_time: dt.time = Field(sa_column=Column(SATime))
    end_time: dt.time = Field(sa_column=Column(SATime))

class UnavailableBlock(UnavailableBlockBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class UnavailableBlockCreate(UnavailableBlockBase):
    pass

class UnavailableBlockRead(UnavailableBlockBase):
    id: int
