from typing import List, Optional
from uuid import UUID
from sqlmodel import Session

from layers.dao import ChatDAO, ChatMessageDAO
from layers.models import Chat, ChatMessage
from layers.schemas import ChatCreate, ChatUpdate, ChatResponse, ChatListResponse
from layers.common import get_current_utc_time


class ChatService:
    """Service layer for Chat operations."""
    
    def __init__(self, session: Session):
        self.session = session
        self.chat_dao = ChatDAO(session)
        self.chat_message_dao = ChatMessageDAO(session)
    
    def create_chat(self, chat_data: ChatCreate) -> ChatResponse:
        """
        Create a new chat session.
        
        Args:
            chat_data: Chat creation data including title, user_id, and optional company_id
            
        Returns:
            Created chat response
            
        Raises:
            ValueError: If user_id is not provided
        """
        if not chat_data.user_id:
            raise ValueError("user_id is required to create a chat")
        
        # Create new chat instance
        new_chat = Chat(
            title=chat_data.title,
            user_id=chat_data.user_id,
            company_id=chat_data.company_id,
            created_at=get_current_utc_time(),
            updated_at=get_current_utc_time()
        )
        
        # Save to database
        created_chat = self.chat_dao.create_chat(new_chat)
        
        # Return response
        return ChatResponse(
            id=created_chat.id,
            title=created_chat.title,
            user_id=created_chat.user_id,
            company_id=created_chat.company_id,
            created_at=created_chat.created_at.isoformat(),
            updated_at=created_chat.updated_at.isoformat()
        )
    
    def delete_chat(self, chat_id: UUID) -> bool:
        """
        Delete a chat session and all its associated messages.
        
        Args:
            chat_id: ID of the chat to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            ValueError: If chat_id is not provided or chat doesn't exist
        """
        if not chat_id:
            raise ValueError("chat_id is required to delete a chat")
        
        # Check if chat exists
        chat = self.chat_dao.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError(f"Chat with ID {chat_id} not found")
        
        # Delete all associated messages first
        self.chat_message_dao.delete_messages_by_chat(chat_id)
        
        # Delete the chat
        success = self.chat_dao.delete_chat(chat_id)
        
        return success
    
    def rename_chat(self, chat_id: UUID, new_title: str) -> ChatResponse:
        """
        Rename a chat session.
        
        Args:
            chat_id: ID of the chat to rename
            new_title: New title for the chat
            
        Returns:
            Updated chat response
            
        Raises:
            ValueError: If chat_id or new_title is not provided, or chat doesn't exist
        """
        if not chat_id:
            raise ValueError("chat_id is required to rename a chat")
        
        if not new_title or not new_title.strip():
            raise ValueError("new_title is required and cannot be empty")
        
        # Update chat title
        updated_chat = self.chat_dao.update_chat_title(chat_id, new_title.strip())
        
        if not updated_chat:
            raise ValueError(f"Chat with ID {chat_id} not found")
        
        # Return response
        return ChatResponse(
            id=updated_chat.id,
            title=updated_chat.title,
            user_id=updated_chat.user_id,
            company_id=updated_chat.company_id,
            created_at=updated_chat.created_at.isoformat(),
            updated_at=updated_chat.updated_at.isoformat()
        )
    
    def get_chat_by_id(self, chat_id: UUID) -> ChatResponse:
        """
        Get a chat by ID.
        
        Args:
            chat_id: ID of the chat to retrieve
            
        Returns:
            Chat response
            
        Raises:
            ValueError: If chat_id is not provided or chat doesn't exist
        """
        if not chat_id:
            raise ValueError("chat_id is required to get a chat")
        
        chat = self.chat_dao.get_chat_by_id(chat_id)
        
        if not chat:
            raise ValueError(f"Chat with ID {chat_id} not found")
        
        return ChatResponse(
            id=chat.id,
            title=chat.title,
            user_id=chat.user_id,
            company_id=chat.company_id,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat()
        )
    
    def get_chats_by_user(self, user_id: UUID) -> ChatListResponse:
        """
        Get all chats for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of chats for the user
            
        Raises:
            ValueError: If user_id is not provided
        """
        if not user_id:
            raise ValueError("user_id is required to get chats")
        
        chats = self.chat_dao.get_chats_by_user(user_id)
        
        return ChatListResponse(
            chats=[
                ChatResponse(
                    id=chat.id,
                    title=chat.title,
                    user_id=chat.user_id,
                    company_id=chat.company_id,
                    created_at=chat.created_at.isoformat(),
                    updated_at=chat.updated_at.isoformat()
                )
                for chat in chats
            ],
            total=len(chats)
        )
    
    def get_chats_by_company(self, company_id: UUID) -> ChatListResponse:
        """
        Get all chats for a specific company.
        
        Args:
            company_id: ID of the company
            
        Returns:
            List of chats for the company
            
        Raises:
            ValueError: If company_id is not provided
        """
        if not company_id:
            raise ValueError("company_id is required to get chats")
        
        chats = self.chat_dao.get_chats_by_company(company_id)
        
        return ChatListResponse(
            chats=[
                ChatResponse(
                    id=chat.id,
                    title=chat.title,
                    user_id=chat.user_id,
                    company_id=chat.company_id,
                    created_at=chat.created_at.isoformat(),
                    updated_at=chat.updated_at.isoformat()
                )
                for chat in chats
            ],
            total=len(chats)
        )
    
    def get_chats_by_user_and_company(self, user_id: UUID, company_id: UUID) -> ChatListResponse:
        """
        Get all chats for a specific user within a company.
        
        Args:
            user_id: ID of the user
            company_id: ID of the company
            
        Returns:
            List of chats for the user within the company
            
        Raises:
            ValueError: If user_id or company_id is not provided
        """
        if not user_id or not company_id:
            raise ValueError("Both user_id and company_id are required")
        
        chats = self.chat_dao.get_chats_by_user_and_company(user_id, company_id)
        
        return ChatListResponse(
            chats=[
                ChatResponse(
                    id=chat.id,
                    title=chat.title,
                    user_id=chat.user_id,
                    company_id=chat.company_id,
                    created_at=chat.created_at.isoformat(),
                    updated_at=chat.updated_at.isoformat()
                )
                for chat in chats
            ],
            total=len(chats)
        )
    
    def get_all_chats(self) -> ChatListResponse:
        """
        Get all chats.
        
        Returns:
            List of all chats
        """
        chats = self.chat_dao.get_all_chats()
        
        return ChatListResponse(
            chats=[
                ChatResponse(
                    id=chat.id,
                    title=chat.title,
                    user_id=chat.user_id,
                    company_id=chat.company_id,
                    created_at=chat.created_at.isoformat(),
                    updated_at=chat.updated_at.isoformat()
                )
                for chat in chats
            ],
            total=len(chats)
        )
    
    def update_chat(self, chat_id: UUID, chat_update: ChatUpdate) -> ChatResponse:
        """
        Update a chat.
        
        Args:
            chat_id: ID of the chat to update
            chat_update: Chat update data
            
        Returns:
            Updated chat response
            
        Raises:
            ValueError: If chat_id is not provided or chat doesn't exist
        """
        if not chat_id:
            raise ValueError("chat_id is required to update a chat")
        
        chat = self.chat_dao.get_chat_by_id(chat_id)
        
        if not chat:
            raise ValueError(f"Chat with ID {chat_id} not found")
        
        # Update fields if provided
        if chat_update.title is not None:
            chat.title = chat_update.title
        
        # Update the updated_at timestamp
        chat.updated_at = get_current_utc_time()
        
        # Save to database
        updated_chat = self.chat_dao.update_chat(chat)
        
        return ChatResponse(
            id=updated_chat.id,
            title=updated_chat.title,
            user_id=updated_chat.user_id,
            company_id=updated_chat.company_id,
            created_at=updated_chat.created_at.isoformat(),
            updated_at=updated_chat.updated_at.isoformat()
        )
