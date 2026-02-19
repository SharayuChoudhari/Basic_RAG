from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional, List
from uuid import UUID

from layers.database import get_db_session
from layers.schemas import ChatCreate, ChatResponse, DocumentListResponse
from services.chat import ChatService
from layers.dao import ChatDAO, DocumentVectorDAO

# Create router
router = APIRouter()


@router.get("/user/{user_id}", response_model=List[ChatResponse])
async def get_chats_by_user(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all chats for a specific user.
    
    Args:
        user_id: ID of the user to get chats for
        session: Database session
        
    Returns:
        List of chat responses
    """
    try:
        chat_dao = ChatDAO(session)
        chats = chat_dao.get_chats_by_user_ordered(user_id)
        return [
            ChatResponse(
                id=chat.id,
                title=chat.title,
                user_id=chat.user_id,
                company_id=chat.company_id,
                created_at=chat.created_at.isoformat(),
                updated_at=chat.updated_at.isoformat()
            )
            for chat in chats
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chats: {str(e)}"
        )


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


@router.get("/documents/company/{company_id}", response_model=DocumentListResponse)
async def get_documents_by_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all unique documents for a specific company.
    
    Args:
        company_id: ID of the company
        session: Database session
        
    Returns:
        List of documents with metadata
    """
    try:
        document_vector_dao = DocumentVectorDAO(session)
        documents = document_vector_dao.get_unique_documents_by_company(company_id)
        
        return DocumentListResponse(
            documents=[
                {
                    "document_id": doc['document_id'],
                    "filename": doc['filename'],
                    "num_chunks": doc['num_chunks'],
                    "created_at": doc['created_at'],
                    "metadata": doc['metadata']
                }
                for doc in documents
            ],
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )
