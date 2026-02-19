from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== Company Schemas ====================

class CompanyCreate(BaseModel):
    """Schema for creating a company."""
    name: str
    description: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_type: str = "local"
    # LLM Configuration
    llm_model: str = "gpt-4"
    llm_provider: str = "openai"
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: Optional[int] = None


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_type: Optional[str] = None
    # LLM Configuration
    llm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None


class CompanyResponse(BaseModel):
    """Schema for company response."""
    id: UUID
    name: str
    description: Optional[str] = None
    embedding_model: str
    embedding_type: str
    # LLM Configuration
    llm_model: str
    llm_provider: str
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_temperature: float
    llm_max_tokens: Optional[int] = None
    created_at: str


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr
    name: str
    company_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company_id: Optional[UUID] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    name: str
    company_id: Optional[UUID] = None
    created_at: str


class UserCompanyResponse(BaseModel):
    """Schema for user's company response."""
    company_id: UUID
    name: str
    description: Optional[str] = None
    embedding_model: str
    embedding_type: str
    # LLM Configuration
    llm_model: str
    llm_provider: str
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_temperature: float
    llm_max_tokens: Optional[int] = None


# ==================== Document Schemas ====================

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    status: str
    document_id: UUID
    filename: str
    text_length: int
    num_chunks: int
    chunk_size: int
    overlap: int
    metadata: dict
    processing_info: Optional[dict] = None


class DocumentPreviewResponse(BaseModel):
    """Schema for document preview response."""
    status: str
    filename: str
    text_length: int
    text_preview: str
    estimated_chunks: int
    metadata: dict


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""
    chunk_index: int
    content: str
    embedding_length: int
    metadata: Optional[dict] = None
    created_at: str


class DocumentGetResponse(BaseModel):
    """Schema for document get response."""
    document_id: UUID
    num_chunks: int
    chunks: List[DocumentChunkResponse]


class DocumentBatchResponse(BaseModel):
    """Schema for batch document upload response."""
    status: str
    total_files: int
    successful: int
    failed: int
    results: List[DocumentUploadResponse]
    errors: List[dict]


class DocumentSearchResult(BaseModel):
    """Schema for document search result."""
    document_id: UUID
    chunk_index: int
    content: str
    similarity_score: float
    metadata: Optional[dict] = None


class DocumentSearchResponse(BaseModel):
    """Schema for document search response."""
    query: str
    num_results: int
    results: List[DocumentSearchResult]

class DocumentInfo(BaseModel):
    """Schema for document information."""
    document_id: UUID
    filename: str
    num_chunks: int
    created_at: str
    metadata: Optional[dict] = None

class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentInfo]
    total: int


# ==================== Common Schemas ====================

class SuccessResponse(BaseModel):
    """Schema for success response."""
    status: str
    message: str


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str


# ==================== Chat Schemas ====================

class ChatCreate(BaseModel):
    """Schema for creating a chat."""
    title: Optional[str] = None
    user_id: UUID
    company_id: Optional[UUID] = None
    # Optional list of document IDs to use for retrieval
    selected_document_ids: Optional[List[UUID]] = None


class ChatUpdate(BaseModel):
    """Schema for updating a chat."""
    title: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: UUID
    title: Optional[str] = None
    user_id: UUID
    company_id: Optional[UUID] = None
    # Selected document IDs
    selected_document_ids: Optional[List[UUID]] = None
    created_at: str
    updated_at: str


class ChatListResponse(BaseModel):
    """Schema for chat list response."""
    chats: List[ChatResponse]
    total: int


# ==================== ChatMessage Schemas ====================

class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""
    chat_id: UUID
    chat_query: str
    context_document: Optional[dict] = None
    response: Optional[str] = None


class ChatMessageUpdate(BaseModel):
    """Schema for updating a chat message."""
    chat_query: Optional[str] = None
    context_document: Optional[dict] = None
    response: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""
    id: UUID
    chat_id: UUID
    chat_query: str
    context_document: Optional[dict] = None
    response: Optional[str] = None
    created_at: str


class ChatMessageListResponse(BaseModel):
    """Schema for chat message list response."""
    messages: List[ChatMessageResponse]
    total: int


class ChatQueryRequest(BaseModel):
    """Schema for chat query request."""
    chat_id: UUID
    query: str
    use_retrieval: bool = True
    top_k: int = 5
    llm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    max_history: int = 10  # Maximum number of previous messages to include in context


class ChatQueryResponse(BaseModel):
    """Schema for chat query response."""
    message_id: UUID
    chat_id: UUID
    query: str
    response: str
    context_documents: List[dict]
    created_at: str
    llm_model: str
    llm_provider: str
