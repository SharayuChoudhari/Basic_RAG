from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

from layers.common import get_current_utc_time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    embedding_model: str = Field(default="all-MiniLM-L6-v2", index=True)
    embedding_type: str = Field(default="local", index=True)  # local, openai, huggingface
    
    # LLM Configuration
    llm_model: str = Field(default="gpt-4", index=True)  # Model name (e.g., "llama2", "mistral", "gpt-4")
    llm_provider: str = Field(default="openai", index=True)  # Provider: openai, anthropic, google, huggingface, ollama, local_hf
    llm_endpoint: Optional[str] = Field(default=None, index=True)  # Endpoint URL for local models (e.g., "http://localhost:11434")
    llm_api_key: Optional[str] = Field(default=None)  # API key for cloud providers (stored securely)
    llm_temperature: float = Field(default=0.7)  # Temperature for generation
    llm_max_tokens: Optional[int] = Field(default=None)  # Max tokens for generation
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to users (one-to-many)
    users: List["User"] = Relationship(back_populates="company")


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Foreign key to company
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id")
    
    # Relationships
    company: Optional[Company] = Relationship(back_populates="users")
    prompts: List["Prompt"] = Relationship(back_populates="user")


class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Foreign key to user
    user_id: UUID = Field(foreign_key="users.id")
    
    # Relationship to user (many-to-one)
    user: User = Relationship(back_populates="prompts")



class DocumentVector(SQLModel, table=True):
    __tablename__ = "document_vectors"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    content: str

    # 👇 IMPORTANT — map to vector(dim)
    # Using variable-length vector to support different embedding models
    embedding: List[float] = Field(sa_column=Column(Vector()))   # Variable-length vector

    meta_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    document_id: UUID = Field(index=True)
    chunk_index: int = Field(default=0)
    user_id: UUID = Field(default_factory=uuid4, index=True)
    company_id: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=get_current_utc_time)


class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)
    
    # Foreign key to user
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    # Optional foreign key to company
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    
    # Selected document IDs for this chat (null/empty means all documents)
    selected_document_ids: Optional[List[UUID]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to chat messages (one-to-many)
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign key to chat
    chat_id: UUID = Field(foreign_key="chats.id", index=True)
    
    # The query given by the user in a given chat session
    chat_query: str = Field(index=True)
    
    # Context document containing retrieved document id or text
    context_document: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    
    # The AI's response to the query
    response: Optional[str] = Field(default=None)
    
    # Status of message processing: "processing" | "done" | "error"
    status: str = Field(default="processing", nullable=False)
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to chat (many-to-one)
    chat: Chat = Relationship(back_populates="chat_messages")


class EvaluationJob(SQLModel, table=True):
    """Tracks batch evaluation runs with aggregated scores."""
    __tablename__ = "evaluation_jobs"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign key to company (company-scoped evaluations)
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    
    # Job status: pending, running, completed, failed
    status: str = Field(default="pending", nullable=False, index=True)
    
    # Total number of queries evaluated
    total_queries: int = Field(default=0)
    
    # Aggregated metric scores
    avg_faithfulness: Optional[float] = Field(default=None)
    avg_answer_relevance: Optional[float] = Field(default=None)
    avg_context_precision: Optional[float] = Field(default=None)
    overall_score: Optional[float] = Field(default=None)
    
    # Timestamps
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Error details if failed
    error_message: Optional[str] = Field(default=None)
    
    # Configuration snapshot used for this job
    config_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to evaluation results (one-to-many)
    results: List["EvaluationResult"] = Relationship(back_populates="job")


class EvaluationResult(SQLModel, table=True):
    """Stores per-query evaluation scores."""
    __tablename__ = "evaluation_results"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign key to evaluation job (nullable for real-time evaluations)
    job_id: Optional[UUID] = Field(default=None, foreign_key="evaluation_jobs.id", index=True)
    
    # Foreign key to chat message (the query being evaluated)
    chat_message_id: Optional[UUID] = Field(default=None, foreign_key="chat_messages.id", index=True)
    
    # Foreign key to company (for filtering)
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    
    # The user query
    question: str = Field(index=True)
    
    # Retrieved document contents
    retrieved_contexts: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    
    # The generated response
    answer: Optional[str] = Field(default=None)
    
    # RAGAS metric scores
    faithfulness_score: Optional[float] = Field(default=None)
    answer_relevance_score: Optional[float] = Field(default=None)
    context_precision_score: Optional[float] = Field(default=None)
    
    # Overall score (average of available metrics)
    overall_score: Optional[float] = Field(default=None)
    
    # Additional metadata
    evaluation_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # Relationship to evaluation job (many-to-one)
    job: Optional[EvaluationJob] = Relationship(back_populates="results")