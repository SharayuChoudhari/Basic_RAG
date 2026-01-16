from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import (
    ChatMessageCreate, ChatMessageUpdate, ChatMessageResponse, 
    ChatMessageListResponse, ChatQueryRequest, ChatQueryResponse
)
from services.chat_messages import ChatMessageService

# Create router
router = APIRouter()


@router.post("/query", response_model=ChatQueryResponse)
async def process_query(
    query_request: ChatQueryRequest,
    session: Session = Depends(get_db_session)
):
    """
    Process a chat query using LangGraph workflow with retrieval and LLM generation.
    
    Args:
        query_request: Query request with chat_id, query, and options
        session: Database session
        
    Returns:
        Query response with message details, context, and LLM info
    """
    try:
        chat_message_service = ChatMessageService(session)
        response = await chat_message_service.process_query(query_request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/", response_model=ChatMessageResponse)
async def create_chat_message(
    message_data: ChatMessageCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new chat message.
    
    Args:
        message_data: Chat message creation data
        session: Database session
        
    Returns:
        Created chat message response
    """
    try:
        chat_message_service = ChatMessageService(session)
        created_message = chat_message_service.create_chat_message(message_data)
        return created_message
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat message: {str(e)}"
        )


@router.get("/{message_id}", response_model=ChatMessageResponse)
async def get_chat_message(
    message_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get a chat message by ID.
    
    Args:
        message_id: ID of the message to retrieve
        session: Database session
        
    Returns:
        Chat message response
    """
    try:
        chat_message_service = ChatMessageService(session)
        message = chat_message_service.get_message_by_id(message_id)
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat message: {str(e)}"
        )


@router.get("/chat/{chat_id}", response_model=ChatMessageListResponse)
async def get_messages_by_chat(
    chat_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all messages for a specific chat.
    
    Args:
        chat_id: ID of the chat
        session: Database session
        
    Returns:
        List of messages for the chat
    """
    try:
        chat_message_service = ChatMessageService(session)
        messages = chat_message_service.get_messages_by_chat(chat_id)
        return messages
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat messages: {str(e)}"
        )


@router.put("/{message_id}", response_model=ChatMessageResponse)
async def update_chat_message(
    message_id: UUID,
    message_update: ChatMessageUpdate,
    session: Session = Depends(get_db_session)
):
    """
    Update a chat message.
    
    Args:
        message_id: ID of the message to update
        message_update: Message update data
        session: Database session
        
    Returns:
        Updated chat message response
    """
    try:
        chat_message_service = ChatMessageService(session)
        updated_message = chat_message_service.update_message(message_id, message_update)
        return updated_message
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update chat message: {str(e)}"
        )


@router.delete("/{message_id}")
async def delete_chat_message(
    message_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete a chat message.
    
    Args:
        message_id: ID of the message to delete
        session: Database session
        
    Returns:
        Deletion status
    """
    try:
        chat_message_service = ChatMessageService(session)
        success = chat_message_service.delete_message(message_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Chat message {message_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Chat message with ID {message_id} not found"
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
            detail=f"Failed to delete chat message: {str(e)}"
        )


@router.delete("/chat/{chat_id}")
async def delete_messages_by_chat(
    chat_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete all messages for a specific chat.
    
    Args:
        chat_id: ID of the chat
        session: Database session
        
    Returns:
        Deletion status with count
    """
    try:
        chat_message_service = ChatMessageService(session)
        count = chat_message_service.delete_messages_by_chat(chat_id)
        
        return {
            "status": "success",
            "message": f"Deleted {count} messages for chat {chat_id}",
            "count": count
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat messages: {str(e)}"
        )
