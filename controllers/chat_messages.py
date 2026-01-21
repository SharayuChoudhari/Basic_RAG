from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional, List
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import ChatQueryRequest, ChatQueryResponse, ChatMessageResponse
from services.chat_messages import ChatMessageService
from layers.dao import ChatMessageDAO

# Create router
router = APIRouter()


@router.get("/chat/{chat_id}", response_model=List[ChatMessageResponse])
async def get_messages_by_chat(
    chat_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all messages for a specific chat, ordered by creation time.
    
    Args:
        chat_id: ID of the chat to get messages for
        session: Database session
        
    Returns:
        List of chat message responses
    """
    try:
        chat_message_dao = ChatMessageDAO(session)
        messages = chat_message_dao.get_messages_by_chat_ordered(chat_id)
        return [
            ChatMessageResponse(
                id=msg.id,
                chat_id=msg.chat_id,
                chat_query=msg.chat_query,
                context_document=msg.context_document,
                response=msg.response,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


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
