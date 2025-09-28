from typing import Optional
from sqlmodel import SQLModel, Field


class EmployeeBase(SQLModel):
    first_name: str
    last_name: str
    email: Optional[str] = None


class Employee(EmployeeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class EmployeeCreate(EmployeeBase):
    pass
