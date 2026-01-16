from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from layers.models import Chat, ChatMessage, User, Company


class ChatDAO:
    """Data Access Object for Chat operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_chat(self, chat: Chat) -> Chat:
        """Create a new chat."""
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat
    
    def get_chat_by_id(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat by ID."""
        statement = select(Chat).where(Chat.id == chat_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_chats(self) -> List[Chat]:
        """Get all chats."""
        statement = select(Chat)
        result = self.session.exec(statement)
        return result.all()
    
    def get_chats_by_user(self, user_id: UUID) -> List[Chat]:
        """Get all chats for a specific user."""
        statement = select(Chat).where(Chat.user_id == user_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_chats_by_company(self, company_id: UUID) -> List[Chat]:
        """Get all chats for a specific company."""
        statement = select(Chat).where(Chat.company_id == company_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_chats_by_user_and_company(self, user_id: UUID, company_id: UUID) -> List[Chat]:
        """Get all chats for a specific user within a company."""
        statement = select(Chat).where(
            Chat.user_id == user_id,
            Chat.company_id == company_id
        )
        result = self.session.exec(statement)
        return result.all()
    
    def update_chat(self, chat: Chat) -> Chat:
        """Update an existing chat."""
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat
    
    def update_chat_title(self, chat_id: UUID, title: str) -> Optional[Chat]:
        """Update the title of a chat."""
        chat = self.get_chat_by_id(chat_id)
        if chat:
            chat.title = title
            self.session.add(chat)
            self.session.commit()
            self.session.refresh(chat)
        return chat
    
    def delete_chat(self, chat_id: UUID) -> bool:
        """Delete a chat by ID."""
        chat = self.get_chat_by_id(chat_id)
        if chat:
            self.session.delete(chat)
            self.session.commit()
            return True
        return False
    
    def get_chat_with_messages(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat with its messages."""
        statement = select(Chat).where(Chat.id == chat_id)
        result = self.session.exec(statement)
        chat = result.first()
        # Access chat_messages to load the relationship
        if chat:
            _ = chat.chat_messages
        return chat
    
    def get_chat_with_user(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat with its user information."""
        statement = select(Chat).where(Chat.id == chat_id)
        result = self.session.exec(statement)
        chat = result.first()
        # Access user to load the relationship
        if chat:
            _ = chat.user
        return chat
    
    def get_chat_with_company(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat with its company information."""
        statement = select(Chat).where(Chat.id == chat_id)
        result = self.session.exec(statement)
        chat = result.first()
        # Access company to load the relationship
        if chat:
            _ = chat.company
        return chat
    
    def get_chat_with_all_relationships(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat with all its relationships (messages, user, company)."""
        statement = select(Chat).where(Chat.id == chat_id)
        result = self.session.exec(statement)
        chat = result.first()
        # Access all relationships to load them
        if chat:
            _ = chat.chat_messages
            _ = chat.user
            _ = chat.company
        return chat
    
    def get_chats_by_user_with_messages(self, user_id: UUID) -> List[Chat]:
        """Get all chats for a user with their messages."""
        statement = select(Chat).where(Chat.user_id == user_id)
        result = self.session.exec(statement)
        chats = result.all()
        # Load messages for each chat
        for chat in chats:
            _ = chat.chat_messages
        return chats
    
    def count_chats_by_user(self, user_id: UUID) -> int:
        """Count the number of chats for a specific user."""
        statement = select(Chat).where(Chat.user_id == user_id)
        result = self.session.exec(statement)
        return len(result.all())
    
    def count_chats_by_company(self, company_id: UUID) -> int:
        """Count the number of chats for a specific company."""
        statement = select(Chat).where(Chat.company_id == company_id)
        result = self.session.exec(statement)
        return len(result.all())
