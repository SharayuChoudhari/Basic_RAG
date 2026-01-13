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
            embedding_type=company.embedding_type
        )
        created_company = company_dao.create_company(new_company)
        
        return CompanyResponse(
            id=created_company.id,
            name=created_company.name,
            description=created_company.description,
            embedding_model=created_company.embedding_model,
            embedding_type=created_company.embedding_type,
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
        
        updated_company = company_dao.update_company(company)
        
        return CompanyResponse(
            id=updated_company.id,
            name=updated_company.name,
            description=updated_company.description,
            embedding_model=updated_company.embedding_model,
            embedding_type=updated_company.embedding_type,
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
            created_at=company.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update embedding model: {str(e)}"
        )
