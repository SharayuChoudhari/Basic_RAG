from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

from layers.common import get_current_utc_time


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    created_at: datetime = Field(default_factory=get_current_utc_time)
