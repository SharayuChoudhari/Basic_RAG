from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
from uuid import UUID

from layers.database import get_db_session
from layers.dao import CompanyDAO
from layers.models import Company
from layers.schemas import CompanyCreate, CompanyUpdate, CompanyResponse

# Create router
router = APIRouter()


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new company.
    
    Args:
        company: Company data to create
        session: Database session
        
    Returns:
        Created company
    """
    try:
        company_dao = CompanyDAO(session)
        new_company = Company(
            name=company.name,
            description=company.description,
            embedding_model=company.embedding_model,
            embedding_type=company.embedding_type,
            # LLM Configuration
            llm_model=company.llm_model,
            llm_provider=company.llm_provider,
            llm_endpoint=company.llm_endpoint,
            llm_api_key=company.llm_api_key,
            llm_temperature=company.llm_temperature,
            llm_max_tokens=company.llm_max_tokens
        )
        created_company = company_dao.create_company(new_company)
        
        return CompanyResponse(
            id=created_company.id,
            name=created_company.name,
            description=created_company.description,
            embedding_model=created_company.embedding_model,
            embedding_type=created_company.embedding_type,
            # LLM Configuration
            llm_model=created_company.llm_model,
            llm_provider=created_company.llm_provider,
            llm_endpoint=created_company.llm_endpoint,
            llm_temperature=created_company.llm_temperature,
            llm_max_tokens=created_company.llm_max_tokens,
            created_at=created_company.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create company: {str(e)}"
        )


@router.get("/", response_model=List[CompanyResponse])
async def get_all_companies(
    session: Session = Depends(get_db_session)
):
    """
    Get all companies.
    
    Args:
        session: Database session
        
    Returns:
        List of all companies
    """
    try:
        company_dao = CompanyDAO(session)
        companies = company_dao.get_all_companies()
        
        return [
            CompanyResponse(
                id=company.id,
                name=company.name,
                description=company.description,
                embedding_model=company.embedding_model,
                embedding_type=company.embedding_type,
                # LLM Configuration
                llm_model=company.llm_model,
                llm_provider=company.llm_provider,
                llm_endpoint=company.llm_endpoint,
                llm_temperature=company.llm_temperature,
                llm_max_tokens=company.llm_max_tokens,
                created_at=company.created_at.isoformat()
            )
            for company in companies
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve companies: {str(e)}"
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get a company by ID.
    
    Args:
        company_id: Company ID
        session: Database session
        
    Returns:
        Company details
    """
    try:
        company_dao = CompanyDAO(session)
        company = company_dao.get_company_by_id(company_id)
        
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            embedding_model=company.embedding_model,
            embedding_type=company.embedding_type,
            # LLM Configuration
            llm_model=company.llm_model,
            llm_provider=company.llm_provider,
            llm_endpoint=company.llm_endpoint,
            llm_temperature=company.llm_temperature,
            llm_max_tokens=company.llm_max_tokens,
            created_at=company.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve company: {str(e)}"
        )


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_update: CompanyUpdate,
    session: Session = Depends(get_db_session)
):
    """
    Update a company.
    
    Args:
        company_id: Company ID
        company_update: Company data to update
        session: Database session
        
    Returns:
        Updated company
    """
    try:
        company_dao = CompanyDAO(session)
        company = company_dao.get_company_by_id(company_id)
        
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Update fields if provided
        if company_update.name is not None:
            company.name = company_update.name
        if company_update.description is not None:
            company.description = company_update.description
        if company_update.embedding_model is not None:
            company.embedding_model = company_update.embedding_model
        if company_update.embedding_type is not None:
            company.embedding_type = company_update.embedding_type
        # Update LLM configuration fields if provided
        if company_update.llm_model is not None:
            company.llm_model = company_update.llm_model
        if company_update.llm_provider is not None:
            company.llm_provider = company_update.llm_provider
        if company_update.llm_endpoint is not None:
            company.llm_endpoint = company_update.llm_endpoint
        if company_update.llm_api_key is not None:
            company.llm_api_key = company_update.llm_api_key
        if company_update.llm_temperature is not None:
            company.llm_temperature = company_update.llm_temperature
        if company_update.llm_max_tokens is not None:
            company.llm_max_tokens = company_update.llm_max_tokens
        
        updated_company = company_dao.update_company(company)
        
        return CompanyResponse(
            id=updated_company.id,
            name=updated_company.name,
            description=updated_company.description,
            embedding_model=updated_company.embedding_model,
            embedding_type=updated_company.embedding_type,
            # LLM Configuration
            llm_model=updated_company.llm_model,
            llm_provider=updated_company.llm_provider,
            llm_endpoint=updated_company.llm_endpoint,
            llm_temperature=updated_company.llm_temperature,
            llm_max_tokens=updated_company.llm_max_tokens,
            created_at=updated_company.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update company: {str(e)}"
        )


@router.delete("/{company_id}")
async def delete_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete a company.
    
    Args:
        company_id: Company ID
        session: Database session
        
    Returns:
        Deletion status
    """
    try:
        company_dao = CompanyDAO(session)
        success = company_dao.delete_company(company_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Company {company_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete company: {str(e)}"
        )


@router.put("/{company_id}/embedding-model")
async def update_company_embedding_model(
    company_id: UUID,
    embedding_model: str,
    embedding_type: str = "local",
    session: Session = Depends(get_db_session)
):
    """
    Update a company's embedding model settings.
    
    Args:
        company_id: Company ID
        embedding_model: Embedding model name
        embedding_type: Embedding type (local, openai, huggingface)
        session: Database session
        
    Returns:
        Updated company
    """
    try:
        company_dao = CompanyDAO(session)
        company = company_dao.update_embedding_model(
            company_id=company_id,
            embedding_model=embedding_model,
            embedding_type=embedding_type
        )
        
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            embedding_model=company.embedding_model,
            embedding_type=company.embedding_type,
            # LLM Configuration
            llm_model=company.llm_model,
            llm_provider=company.llm_provider,
            llm_endpoint=company.llm_endpoint,
            llm_temperature=company.llm_temperature,
            llm_max_tokens=company.llm_max_tokens,
            created_at=company.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update embedding model: {str(e)}"
        )


@router.put("/{company_id}/llm-config")
async def update_company_llm_config(
    company_id: UUID,
    llm_model: str,
    llm_provider: str,
    llm_endpoint: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_temperature: float = 0.7,
    llm_max_tokens: Optional[int] = None,
    session: Session = Depends(get_db_session)
):
    """
    Update a company's LLM configuration settings.
    
    Args:
        company_id: Company ID
        llm_model: LLM model name (e.g., "llama2", "mistral", "gpt-4")
        llm_provider: LLM provider (openai, anthropic, google, huggingface, ollama, local_hf)
        llm_endpoint: Optional endpoint URL for local models (e.g., "http://localhost:11434")
        llm_api_key: Optional API key for cloud providers
        llm_temperature: Temperature for generation (default: 0.7)
        llm_max_tokens: Optional max tokens for generation
        session: Database session
        
    Returns:
        Updated company
    """
    try:
        company_dao = CompanyDAO(session)
        llm_config = {
            "llm_model": llm_model,
            "llm_provider": llm_provider,
            "llm_endpoint": llm_endpoint,
            "llm_api_key": llm_api_key,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens
        }
        company = company_dao.update_llm_config(company_id=company_id, llm_config=llm_config)
        
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            embedding_model=company.embedding_model,
            embedding_type=company.embedding_type,
            # LLM Configuration
            llm_model=company.llm_model,
            llm_provider=company.llm_provider,
            llm_endpoint=company.llm_endpoint,
            llm_temperature=company.llm_temperature,
            llm_max_tokens=company.llm_max_tokens,
            created_at=company.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update LLM configuration: {str(e)}"
        )
