from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
from uuid import UUID

from layers.database import get_db_session
from layers.dao import UserDAO
from layers.models import User
from layers.schemas import UserCreate, UserUpdate, UserResponse, UserCompanyResponse

# Create router
router = APIRouter()


@router.get("/company/{company_id}", response_model=List[UserResponse])
async def get_users_by_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all users for a specific company.
    
    Args:
        company_id: ID of the company to get users for
        session: Database session
        
    Returns:
        List of user responses
    """
    try:
        user_dao = UserDAO(session)
        users = user_dao.get_users_by_company(company_id)
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                company_id=user.company_id,
                created_at=user.created_at.isoformat()
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new user.
    
    Args:
        user: User data to create
        session: Database session
        
    Returns:
        Created user
    """
    try:
        user_dao = UserDAO(session)
        new_user = User(
            email=user.email,
            name=user.name,
            company_id=user.company_id
        )
        created_user = user_dao.create_user(new_user)
        
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            name=created_user.name,
            company_id=created_user.company_id,
            created_at=created_user.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    session: Session = Depends(get_db_session)
):
    """
    Get all users.
    
    Args:
        session: Database session
        
    Returns:
        List of all users
    """
    try:
        user_dao = UserDAO(session)
        users = user_dao.get_all_users()
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                company_id=user.company_id,
                created_at=user.created_at.isoformat()
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get a user by ID.
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        User details
    """
    try:
        user_dao = UserDAO(session)
        user = user_dao.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            company_id=user.company_id,
            created_at=user.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    session: Session = Depends(get_db_session)
):
    """
    Get a user by email.
    
    Args:
        email: User email
        session: Database session
        
    Returns:
        User details
    """
    try:
        user_dao = UserDAO(session)
        user = user_dao.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with email {email} not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            company_id=user.company_id,
            created_at=user.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    session: Session = Depends(get_db_session)
):
    """
    Update a user.
    
    Args:
        user_id: User ID
        user_update: User data to update
        session: Database session
        
    Returns:
        Updated user
    """
    try:
        user_dao = UserDAO(session)
        user = user_dao.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Update fields if provided
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.company_id is not None:
            user.company_id = user_update.company_id
        
        updated_user = user_dao.update_user(user)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            company_id=updated_user.company_id,
            created_at=updated_user.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete a user.
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        Deletion status
    """
    try:
        user_dao = UserDAO(session)
        success = user_dao.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"User {user_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/{user_id}/company")
async def get_user_company(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get the company associated with a user.
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        Company details
    """
    try:
        user_dao = UserDAO(session)
        user = user_dao.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        if not user.company:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} is not associated with any company"
            )
        
        return {
            "company_id": user.company.id,
            "name": user.company.name,
            "description": user.company.description,
            "embedding_model": user.company.embedding_model,
            "embedding_type": user.company.embedding_type,
            # LLM Configuration
            "llm_model": user.company.llm_model,
            "llm_provider": user.company.llm_provider,
            "llm_endpoint": user.company.llm_endpoint,
            "llm_temperature": user.company.llm_temperature,
            "llm_max_tokens": user.company.llm_max_tokens
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user's company: {str(e)}"
        )
