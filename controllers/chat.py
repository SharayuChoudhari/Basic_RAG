from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import ChatCreate, ChatResponse
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
        new_title: New title for the chat (default: first 8 words of the first query)
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
