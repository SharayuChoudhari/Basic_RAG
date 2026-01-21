from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import ChatQueryRequest, ChatQueryResponse
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
