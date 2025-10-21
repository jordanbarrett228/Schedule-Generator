from sqlmodel import SQLModel
from typing import Optional
from sqlmodel import Field
import sqlalchemy

schedulemetadata = sqlalchemy.MetaData()

class DBBase(SQLModel):
    user_id: Optional[int] = Field(default=None, index=True, description="ID of the user")
    metadata = schedulemetadata