from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlmodel import Session
from typing import Optional, Dict, Any, List
from uuid import UUID
import os
from pypdf import PdfReader
import io
import json

from layers.database import get_db_session
from services.document_embedding import DocumentEmbeddingService
from services.vectorizer import VectorizerFactory
from layers.dao import CompanyDAO
from layers.models import Company
from layers.schemas import (
    DocumentUploadResponse,
    DocumentPreviewResponse,
    DocumentGetResponse,
    DocumentBatchResponse,
    DocumentSearchResponse
)

# Create router
router = APIRouter()

# Get default vectorizer type from environment variable, default to local
DEFAULT_VECTORIZER_TYPE = os.getenv("VECTORIZER_TYPE", "local")
DEFAULT_VECTORIZER_MODEL = os.getenv("VECTORIZER_MODEL", "all-MiniLM-L6-v2")

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB default max file size
ALLOWED_MIME_TYPES = ["application/pdf"]


def get_company_embedding_settings(
    company_id: Optional[UUID],
    session: Session
) -> tuple[str, str]:
    """
    Get embedding model settings for a company.
    
    Args:
        company_id: Company ID (optional)
        session: Database session
        
    Returns:
        Tuple of (embedding_model, embedding_type)
    """
    if company_id:
        company_dao = CompanyDAO(session)
        settings = company_dao.get_embedding_model(company_id)
        if settings:
            return settings
    
    # Return defaults if no company or no settings found
    return (DEFAULT_VECTORIZER_MODEL, DEFAULT_VECTORIZER_TYPE)


def get_document_embedding_service(
    company_id: Optional[UUID] = None,
    session: Session = Depends(get_db_session)
) -> DocumentEmbeddingService:
    """
    Dependency to get DocumentEmbeddingService instance with company-specific settings.
    
    Args:
        company_id: Optional company ID to get embedding settings from
        session: Database session
        
    Returns:
        DocumentEmbeddingService instance
    """
    # Get embedding settings from company or use defaults
    embedding_model, embedding_type = get_company_embedding_settings(company_id, session)
    
    # Create vectorizer with company-specific settings
    vectorizer = VectorizerFactory.create_vectorizer(
        vectorizer_type=embedding_type,
        model=embedding_model
    )
    return DocumentEmbeddingService(session=session, vectorizer=vectorizer)


def get_document_embedding_service_with_company(
    company_id: Optional[UUID] = None,
    session: Session = Depends(get_db_session)
) -> DocumentEmbeddingService:
    """
    Dependency wrapper that allows company_id to be passed from endpoint parameters.
    
    Args:
        company_id: Optional company ID to get embedding settings from
        session: Database session
        
    Returns:
        DocumentEmbeddingService instance
    """
    return get_document_embedding_service(company_id, session)


def validate_pdf_file(pdf_file: UploadFile) -> None:
    """
    Validate PDF file before processing.
    
    Args:
        pdf_file: The uploaded PDF file
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Check content type
    if pdf_file.content_type and pdf_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Expected: {ALLOWED_MIME_TYPES}, Got: {pdf_file.content_type}"
        )
    
    # Check file size
    file_size = 0
    if hasattr(pdf_file.file, 'seek'):
        pdf_file.file.seek(0, 2)  # Seek to end
        file_size = pdf_file.file.tell()
        pdf_file.file.seek(0)  # Seek back to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )


def extract_pdf_metadata(pdf_reader: PdfReader) -> Dict[str, Any]:
    """
    Extract metadata from PDF file.
    
    Args:
        pdf_reader: PdfReader instance
        
    Returns:
        Dictionary containing PDF metadata
    """
    metadata = {}
    
    # Extract PDF metadata
    if pdf_reader.metadata:
        metadata.update({
            "title": pdf_reader.metadata.get("/Title", ""),
            "author": pdf_reader.metadata.get("/Author", ""),
            "subject": pdf_reader.metadata.get("/Subject", ""),
            "creator": pdf_reader.metadata.get("/Creator", ""),
            "producer": pdf_reader.metadata.get("/Producer", ""),
            "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
            "modification_date": str(pdf_reader.metadata.get("/ModDate", ""))
        })
    
    # Add page count
    metadata["page_count"] = len(pdf_reader.pages)
    
    return metadata


def extract_text_from_pdf(pdf_file: UploadFile) -> tuple[str, Dict[str, Any]]:
    """
    Extract text and metadata from a PDF file.
    
    Args:
        pdf_file: The uploaded PDF file
        
    Returns:
        Tuple of (extracted text, metadata dictionary)
    """
    try:
        # Read the file content
        pdf_content = pdf_file.file.read()
        
        # Create a PDF reader from the bytes
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        
        # Extract metadata
        metadata = extract_pdf_metadata(pdf_reader)
        
        # Extract text from all pages
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return text.strip(), metadata
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    company_id: Optional[UUID] = Form(None, description="Company ID (optional, uses company's embedding model settings)"),
    user_id: Optional[UUID] = Form(None, description="User ID (optional)"),
    chunk_size: int = Form(1000, description="Size of each chunk in characters"),
    overlap: int = Form(200, description="Overlap between chunks in characters"),
    metadata: Optional[str] = Form(None, description="Additional metadata as JSON string"),
    preview_only: bool = Form(False, description="If true, only preview extracted text without creating embeddings"),
    skip_empty_chunks: bool = Form(True, description="Skip chunks with no text content"),
    clean_text: bool = Form(True, description="Clean and normalize text before processing"),
    document_embedding_service: DocumentEmbeddingService = Depends(get_document_embedding_service_with_company)
):
    """
    Upload a PDF file, extract text, create embeddings, and store in database.
    
    Enhanced features:
    - File validation (size, type, content)
    - PDF metadata extraction (title, author, page count, etc.)
    - Preview mode to see extracted text before processing
    - Text cleaning and normalization
    - Skip empty chunks option
    
    Args:
        file: PDF file to upload
        user_id: Optional user ID for the document
        chunk_size: Size of each chunk in characters (default: 1000)
        overlap: Overlap between chunks in characters (default: 200)
        metadata: Optional metadata as JSON string
        preview_only: If true, return preview without creating embeddings
        skip_empty_chunks: Skip chunks with no text content (default: true)
        clean_text: Clean and normalize text before processing (default: true)
        document_embedding_service: Document embedding service (injected)
        
    Returns:
        Document ID and processing information, or preview if preview_only is true
    """
    # Validate PDF file
    validate_pdf_file(file)
    
    # Extract text and metadata from PDF
    text, pdf_metadata = extract_text_from_pdf(file)
    
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the PDF"
        )
    
    # Clean text if requested
    if clean_text:
        text = clean_text_content(text)
    
    # Parse additional metadata if provided
    parsed_metadata: Dict[str, Any] = {
        "filename": file.filename,
        "file_size": file.file.seek(0, 2) if hasattr(file.file, 'seek') else 0,
        "pdf_metadata": pdf_metadata
    }
    
    # Reset file pointer
    if hasattr(file.file, 'seek'):
        file.file.seek(0)
    
    if metadata:
        try:
            parsed_metadata.update(json.loads(metadata))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON format for metadata"
            )
    
    # If preview only, return extracted text without processing
    if preview_only:
        return DocumentPreviewResponse(
            status="preview",
            filename=file.filename,
            text_length=len(text),
            text_preview=text[:1000] + "..." if len(text) > 1000 else text,
            estimated_chunks=max(1, len(text) // (chunk_size - overlap)),
            metadata=parsed_metadata
        )
    
    # Process document and create embeddings
    try:
        document_id = document_embedding_service.process_document(
            text=text,
            user_id=user_id or 0,
            company_id=company_id,
            chunk_size=chunk_size,
            overlap=overlap,
            metadata=parsed_metadata
        )
        
        # Get the number of chunks created
        chunks = document_embedding_service.get_document_chunks(document_id)
        
        # Filter empty chunks if requested
        if skip_empty_chunks:
            chunks = [c for c in chunks if c.content.strip()]
        
        return DocumentUploadResponse(
            status="success",
            document_id=document_id,
            filename=file.filename,
            text_length=len(text),
            num_chunks=len(chunks),
            chunk_size=chunk_size,
            overlap=overlap,
            metadata=parsed_metadata,
            processing_info={
                "pages_processed": pdf_metadata.get("page_count", 0),
                "text_cleaned": clean_text,
                "empty_chunks_skipped": skip_empty_chunks
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/upload/batch")
async def upload_pdf_batch(
    files: List[UploadFile] = File(..., description="Multiple PDF files to upload"),
    company_id: Optional[UUID] = Form(None, description="Company ID (optional, uses company's embedding model settings)"),
    user_id: Optional[UUID] = Form(None, description="User ID (optional)"),
    chunk_size: int = Form(1000, description="Size of each chunk in characters"),
    overlap: int = Form(200, description="Overlap between chunks in characters"),
    metadata: Optional[str] = Form(None, description="Additional metadata as JSON string (applied to all files)"),
    skip_empty_chunks: bool = Form(True, description="Skip chunks with no text content"),
    clean_text: bool = Form(True, description="Clean and normalize text before processing"),
    document_embedding_service: DocumentEmbeddingService = Depends(get_document_embedding_service_with_company)
):
    """
    Upload multiple PDF files in batch, extract text, create embeddings, and store in database.
    
    Args:
        files: List of PDF files to upload
        user_id: Optional user ID for the documents
        chunk_size: Size of each chunk in characters (default: 1000)
        overlap: Overlap between chunks in characters (default: 200)
        metadata: Optional metadata as JSON string (applied to all files)
        skip_empty_chunks: Skip chunks with no text content (default: true)
        clean_text: Clean and normalize text before processing (default: true)
        document_embedding_service: Document embedding service (injected)
        
    Returns:
        List of processing results for each file
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files can be uploaded in a single batch"
        )
    
    # Parse metadata if provided
    parsed_metadata: Optional[Dict[str, Any]] = None
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON format for metadata"
            )
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Validate PDF file
            validate_pdf_file(file)
            
            # Extract text and metadata from PDF
            text, pdf_metadata = extract_text_from_pdf(file)
            
            if not text:
                errors.append({
                    "filename": file.filename,
                    "error": "No text could be extracted from the PDF"
                })
                continue
            
            # Clean text if requested
            if clean_text:
                text = clean_text_content(text)
            
            # Build metadata for this file
            file_metadata = {
                "filename": file.filename,
                "file_size": file.file.seek(0, 2) if hasattr(file.file, 'seek') else 0,
                "pdf_metadata": pdf_metadata
            }
            
            # Reset file pointer
            if hasattr(file.file, 'seek'):
                file.file.seek(0)
            
            # Add custom metadata if provided
            if parsed_metadata:
                file_metadata.update(parsed_metadata)
            
            # Process document and create embeddings
            document_id = document_embedding_service.process_document(
                text=text,
                user_id=user_id or 0,
                company_id=company_id,
                chunk_size=chunk_size,
                overlap=overlap,
                metadata=file_metadata
            )
            
            # Get the number of chunks created
            chunks = document_embedding_service.get_document_chunks(document_id)
            
            # Filter empty chunks if requested
            if skip_empty_chunks:
                chunks = [c for c in chunks if c.content.strip()]
            
            results.append({
                "status": "success",
                "document_id": document_id,
                "filename": file.filename,
                "text_length": len(text),
                "num_chunks": len(chunks),
                "metadata": file_metadata
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return DocumentBatchResponse(
        status="completed",
        total_files=len(files),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors
    )


def clean_text_content(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']', '', text)
    
    # Remove page markers
    text = re.sub(r'--- Page \d+ ---', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    company_id: Optional[UUID] = None,
    document_embedding_service: DocumentEmbeddingService = Depends(get_document_embedding_service_with_company)
):
    """
    Get all chunks for a specific document.
    
    Args:
        document_id: The document ID
        document_embedding_service: Document embedding service (injected)
        
    Returns:
        List of document chunks with embeddings
    """
    try:
        chunks = document_embedding_service.get_document_chunks(document_id)
        
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        return DocumentGetResponse(
            document_id=document_id,
            num_chunks=len(chunks),
            chunks=[
                {
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding_length": len(chunk.embedding),
                    "metadata": chunk.meta_data,
                    "created_at": chunk.created_at.isoformat()
                }
                for chunk in chunks
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    company_id: Optional[UUID] = None,
    document_embedding_service: DocumentEmbeddingService = Depends(get_document_embedding_service_with_company)
):
    """
    Delete a document and all its chunks.
    
    Args:
        document_id: The document ID
        document_embedding_service: Document embedding service (injected)
        
    Returns:
        Deletion status
    """
    try:
        success = document_embedding_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/search")
async def search_documents(
    query: str = Form(..., description="Search query text"),
    company_id: Optional[UUID] = Form(None, description="Company ID (optional, uses company's embedding model settings)"),
    user_id: Optional[UUID] = Form(None, description="User ID to filter by (optional)"),
    limit: int = Form(5, description="Maximum number of results"),
    document_embedding_service: DocumentEmbeddingService = Depends(get_document_embedding_service_with_company)
):
    """
    Search for similar documents using vector similarity.
    
    Args:
        query: The search query text
        user_id: Optional user ID to filter by
        limit: Maximum number of results (default: 5)
        document_embedding_service: Document embedding service (injected)
        
    Returns:
        List of similar documents with similarity scores
    """
    try:
        results = document_embedding_service.search_similar_documents(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        return DocumentSearchResponse(
            query=query,
            num_results=len(results),
            results=[
                {
                    "document_id": vector.document_id,
                    "chunk_index": vector.chunk_index,
                    "content": vector.content,
                    "similarity_score": score,
                    "metadata": vector.meta_data
                }
                for vector, score in results
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}"
        )
