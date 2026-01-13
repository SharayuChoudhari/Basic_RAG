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


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_type: Optional[str] = None


class CompanyResponse(BaseModel):
    """Schema for company response."""
    id: UUID
    name: str
    description: Optional[str] = None
    embedding_model: str
    embedding_type: str
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
