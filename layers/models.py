from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

from layers.common import get_current_utc_time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    embedding_model: str = Field(default="all-MiniLM-L6-v2", index=True)
    embedding_type: str = Field(default="local", index=True)  # local, openai, huggingface
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to users (one-to-many)
    users: List["User"] = Relationship(back_populates="company")


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Foreign key to company
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    
    # Relationships
    company: Optional[Company] = Relationship(back_populates="users")
    prompts: List["Prompt"] = Relationship(back_populates="user")


class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Foreign key to user
    user_id: int = Field(foreign_key="users.id")
    
    # Relationship to user (many-to-one)
    user: User = Relationship(back_populates="prompts")



class DocumentVector(SQLModel, table=True):
    __tablename__ = "document_vectors"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str

    # 👇 IMPORTANT — map to vector(dim)
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))   # <-- set your dimension

    meta_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    document_id: str = Field(index=True)
    chunk_index: int = Field(default=0)
    user_id: int = Field(default=0, index=True)
    company_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=get_current_utc_time)