from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import ChatCreate, ChatUpdate, ChatResponse, ChatListResponse
from services.chat import ChatService

# Create router
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new chat session.
    
    Args:
        chat_data: Chat creation data including title, user_id, and optional company_id
        session: Database session
        
    Returns:
        Created chat response
    """
    try:
        chat_service = ChatService(session)
        created_chat = chat_service.create_chat(chat_data)
        return created_chat
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat: {str(e)}"
        )


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete a chat session and all its associated messages.
    
    Args:
        chat_id: ID of the chat to delete
        session: Database session
        
    Returns:
        Deletion status
    """
    try:
        chat_service = ChatService(session)
        success = chat_service.delete_chat(chat_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Chat {chat_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Chat with ID {chat_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat: {str(e)}"
        )


@router.put("/{chat_id}/rename", response_model=ChatResponse)
async def rename_chat(
    chat_id: UUID,
    new_title: str,
    session: Session = Depends(get_db_session)
):
    """
    Rename a chat session.
    
    Args:
        chat_id: ID of the chat to rename
        new_title: New title for the chat
        session: Database session
        
    Returns:
        Updated chat response
    """
    try:
        chat_service = ChatService(session)
        updated_chat = chat_service.rename_chat(chat_id, new_title)
        return updated_chat
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rename chat: {str(e)}"
        )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get a chat by ID.
    
    Args:
        chat_id: ID of the chat to retrieve
        session: Database session
        
    Returns:
        Chat response
    """
    try:
        chat_service = ChatService(session)
        chat = chat_service.get_chat_by_id(chat_id)
        return chat
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat: {str(e)}"
        )


@router.get("/", response_model=ChatListResponse)
async def get_all_chats(
    session: Session = Depends(get_db_session)
):
    """
    Get all chats.
    
    Args:
        session: Database session
        
    Returns:
        List of all chats
    """
    try:
        chat_service = ChatService(session)
        chats = chat_service.get_all_chats()
        return chats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chats: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=ChatListResponse)
async def get_chats_by_user(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all chats for a specific user.
    
    Args:
        user_id: ID of the user
        session: Database session
        
    Returns:
        List of chats for the user
    """
    try:
        chat_service = ChatService(session)
        chats = chat_service.get_chats_by_user(user_id)
        return chats
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chats: {str(e)}"
        )


@router.get("/company/{company_id}", response_model=ChatListResponse)
async def get_chats_by_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all chats for a specific company.
    
    Args:
        company_id: ID of the company
        session: Database session
        
    Returns:
        List of chats for the company
    """
    try:
        chat_service = ChatService(session)
        chats = chat_service.get_chats_by_company(company_id)
        return chats
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chats: {str(e)}"
        )


@router.get("/user/{user_id}/company/{company_id}", response_model=ChatListResponse)
async def get_chats_by_user_and_company(
    user_id: UUID,
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all chats for a specific user within a company.
    
    Args:
        user_id: ID of the user
        company_id: ID of the company
        session: Database session
        
    Returns:
        List of chats for the user within the company
    """
    try:
        chat_service = ChatService(session)
        chats = chat_service.get_chats_by_user_and_company(user_id, company_id)
        return chats
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chats: {str(e)}"
        )


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: UUID,
    chat_update: ChatUpdate,
    session: Session = Depends(get_db_session)
):
    """
    Update a chat.
    
    Args:
        chat_id: ID of the chat to update
        chat_update: Chat update data
        session: Database session
        
    Returns:
        Updated chat response
    """
    try:
        chat_service = ChatService(session)
        updated_chat = chat_service.update_chat(chat_id, chat_update)
        return updated_chat
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update chat: {str(e)}"
        )
