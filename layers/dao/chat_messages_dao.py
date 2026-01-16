from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from layers.models import ChatMessage, Chat


class ChatMessageDAO:
    """Data Access Object for ChatMessage operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_chat_message(self, chat_message: ChatMessage) -> ChatMessage:
        """Create a new chat message."""
        self.session.add(chat_message)
        self.session.commit()
        self.session.refresh(chat_message)
        return chat_message
    
    def get_chat_message_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get a chat message by ID."""
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_chat_messages(self) -> List[ChatMessage]:
        """Get all chat messages."""
        statement = select(ChatMessage)
        result = self.session.exec(statement)
        return result.all()
    
    def get_messages_by_chat(self, chat_id: UUID) -> List[ChatMessage]:
        """Get all messages for a specific chat."""
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_messages_by_chat_ordered(self, chat_id: UUID) -> List[ChatMessage]:
        """Get all messages for a specific chat ordered by creation time."""
        statement = select(ChatMessage).where(
            ChatMessage.chat_id == chat_id
        ).order_by(ChatMessage.created_at)
        result = self.session.exec(statement)
        return result.all()
    
    def get_messages_by_query(self, query: str) -> List[ChatMessage]:
        """Get all messages matching a specific query."""
        statement = select(ChatMessage).where(ChatMessage.chat_query == query)
        result = self.session.exec(statement)
        return result.all()
    
    def get_messages_by_chat_and_query(self, chat_id: UUID, query: str) -> List[ChatMessage]:
        """Get messages for a specific chat matching a query."""
        statement = select(ChatMessage).where(
            ChatMessage.chat_id == chat_id,
            ChatMessage.chat_query == query
        )
        result = self.session.exec(statement)
        return result.all()
    
    def update_chat_message(self, chat_message: ChatMessage) -> ChatMessage:
        """Update an existing chat message."""
        self.session.add(chat_message)
        self.session.commit()
        self.session.refresh(chat_message)
        return chat_message
    
    def update_message_response(self, message_id: UUID, response: str) -> Optional[ChatMessage]:
        """Update the response of a chat message."""
        message = self.get_chat_message_by_id(message_id)
        if message:
            message.response = response
            self.session.add(message)
            self.session.commit()
            self.session.refresh(message)
        return message
    
    def update_message_context(self, message_id: UUID, context_document: dict) -> Optional[ChatMessage]:
        """Update the context document of a chat message."""
        message = self.get_chat_message_by_id(message_id)
        if message:
            message.context_document = context_document
            self.session.add(message)
            self.session.commit()
            self.session.refresh(message)
        return message
    
    def delete_chat_message(self, message_id: UUID) -> bool:
        """Delete a chat message by ID."""
        message = self.get_chat_message_by_id(message_id)
        if message:
            self.session.delete(message)
            self.session.commit()
            return True
        return False
    
    def delete_messages_by_chat(self, chat_id: UUID) -> int:
        """Delete all messages for a specific chat. Returns the number of messages deleted."""
        messages = self.get_messages_by_chat(chat_id)
        count = len(messages)
        for message in messages:
            self.session.delete(message)
        self.session.commit()
        return count
    
    def get_message_with_chat(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get a chat message with its chat information."""
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        result = self.session.exec(statement)
        message = result.first()
        # Access chat to load the relationship
        if message:
            _ = message.chat
        return message
    
    def get_messages_with_chat(self, chat_id: UUID) -> List[ChatMessage]:
        """Get all messages for a chat with the chat relationship loaded."""
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat_id)
        result = self.session.exec(statement)
        messages = result.all()
        # Load chat relationship for each message
        for message in messages:
            _ = message.chat
        return messages
    
    def count_messages_by_chat(self, chat_id: UUID) -> int:
        """Count the number of messages for a specific chat."""
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat_id)
        result = self.session.exec(statement)
        return len(result.all())
    
    def get_latest_message_by_chat(self, chat_id: UUID) -> Optional[ChatMessage]:
        """Get the latest message for a specific chat."""
        statement = select(ChatMessage).where(
            ChatMessage.chat_id == chat_id
        ).order_by(ChatMessage.created_at.desc())
        result = self.session.exec(statement)
        return result.first()
    
    def get_messages_without_response(self, chat_id: Optional[UUID] = None) -> List[ChatMessage]:
        """Get all messages that don't have a response yet.
        
        Args:
            chat_id: Optional chat ID to filter messages for a specific chat.
                    If None, returns all messages without response.
        """
        statement = select(ChatMessage).where(ChatMessage.response == None)
        if chat_id:
            statement = statement.where(ChatMessage.chat_id == chat_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_messages_with_context(self, chat_id: Optional[UUID] = None) -> List[ChatMessage]:
        """Get all messages that have context documents.
        
        Args:
            chat_id: Optional chat ID to filter messages for a specific chat.
                    If None, returns all messages with context.
        """
        statement = select(ChatMessage).where(ChatMessage.context_document != None)
        if chat_id:
            statement = statement.where(ChatMessage.chat_id == chat_id)
        result = self.session.exec(statement)
        return result.all()
