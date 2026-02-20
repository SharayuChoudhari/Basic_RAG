"""Dataset loader for evaluation pipeline.

This module loads evaluation data from the ChatMessage database table
and converts it to EvaluationInput format for the RAGAS evaluator.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, and_

from layers.models import ChatMessage, Chat
from evaluations.schemas import EvaluationInput


class DatasetLoader:
    """Loads evaluation data from ChatMessage database.
    
    This class provides methods to load ChatMessage records and convert
    them to EvaluationInput objects for evaluation.
    
    Attributes:
        session: SQLModel database session.
        company_id: Optional company ID for filtering.
    """
    
    def __init__(self, session: Session, company_id: Optional[UUID] = None):
        """Initialize the dataset loader.
        
        Args:
            session: SQLModel database session.
            company_id: Optional company ID to filter messages.
        """
        self.session = session
        self.company_id = company_id
    
    def load_messages(
        self,
        chat_ids: Optional[List[UUID]] = None,
        user_ids: Optional[List[UUID]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: Optional[int] = None,
        require_response: bool = True,
        require_context: bool = True,
    ) -> List[EvaluationInput]:
        """Load ChatMessage records and convert to evaluation inputs.
        
        Args:
            chat_ids: Optional list of chat IDs to filter by.
            user_ids: Optional list of user IDs to filter by.
            date_range: Optional tuple of (start_date, end_date).
            limit: Optional maximum number of messages to load.
            require_response: Only include messages with responses.
            require_context: Only include messages with context documents.
        
        Returns:
            List of EvaluationInput objects ready for evaluation.
        """
        # Build query
        statement = select(ChatMessage).join(Chat)
        
        # Apply filters
        conditions = []
        
        # Filter by company
        if self.company_id:
            conditions.append(Chat.company_id == self.company_id)
        
        # Filter by chat IDs
        if chat_ids:
            conditions.append(ChatMessage.chat_id.in_(chat_ids))
        
        # Filter by user IDs
        if user_ids:
            conditions.append(Chat.user_id.in_(user_ids))
        
        # Filter by date range
        if date_range:
            start_date, end_date = date_range
            conditions.append(ChatMessage.created_at >= start_date)
            conditions.append(ChatMessage.created_at <= end_date)
        
        # Filter by response existence
        if require_response:
            conditions.append(ChatMessage.response.is_not(None))
            conditions.append(ChatMessage.response != "")
        
        # Filter by context existence
        if require_context:
            conditions.append(ChatMessage.context_document.is_not(None))
        
        # Apply all conditions
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # Order by creation time
        statement = statement.order_by(ChatMessage.created_at.desc())
        
        # Apply limit
        if limit:
            statement = statement.limit(limit)
        
        # Execute query
        results = self.session.exec(statement)
        messages = results.all()
        
        # Convert to EvaluationInput
        return [self._convert_to_input(msg) for msg in messages]
    
    def load_single_message(self, message_id: UUID) -> Optional[EvaluationInput]:
        """Load a single ChatMessage for per-query evaluation.
        
        Args:
            message_id: UUID of the ChatMessage to load.
        
        Returns:
            EvaluationInput if found, None otherwise.
        """
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        result = self.session.exec(statement)
        message = result.first()
        
        if message:
            return self._convert_to_input(message)
        return None
    
    def load_messages_by_chat(self, chat_id: UUID) -> List[EvaluationInput]:
        """Load all messages from a specific chat.
        
        Args:
            chat_id: UUID of the chat.
        
        Returns:
            List of EvaluationInput objects from the chat.
        """
        statement = (
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.asc())
        )
        results = self.session.exec(statement)
        messages = results.all()
        
        return [self._convert_to_input(msg) for msg in messages]
    
    def load_messages_by_user(
        self,
        user_id: UUID,
        limit: Optional[int] = None
    ) -> List[EvaluationInput]:
        """Load messages from a specific user.
        
        Args:
            user_id: UUID of the user.
            limit: Optional maximum number of messages.
        
        Returns:
            List of EvaluationInput objects from the user.
        """
        statement = (
            select(ChatMessage)
            .join(Chat)
            .where(Chat.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
        )
        
        if limit:
            statement = statement.limit(limit)
        
        results = self.session.exec(statement)
        messages = results.all()
        
        return [self._convert_to_input(msg) for msg in messages]
    
    def get_message_count(
        self,
        chat_ids: Optional[List[UUID]] = None,
        user_ids: Optional[List[UUID]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> int:
        """Get count of messages matching filters.
        
        Useful for previewing how many messages will be evaluated.
        
        Args:
            chat_ids: Optional list of chat IDs to filter by.
            user_ids: Optional list of user IDs to filter by.
            date_range: Optional tuple of (start_date, end_date).
        
        Returns:
            Count of matching messages.
        """
        statement = select(ChatMessage).join(Chat)
        
        conditions = []
        
        if self.company_id:
            conditions.append(Chat.company_id == self.company_id)
        
        if chat_ids:
            conditions.append(ChatMessage.chat_id.in_(chat_ids))
        
        if user_ids:
            conditions.append(Chat.user_id.in_(user_ids))
        
        if date_range:
            start_date, end_date = date_range
            conditions.append(ChatMessage.created_at >= start_date)
            conditions.append(ChatMessage.created_at <= end_date)
        
        # Only count messages with responses and context
        conditions.append(ChatMessage.response.is_not(None))
        conditions.append(ChatMessage.context_document.is_not(None))
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        results = self.session.exec(statement)
        return len(results.all())
    
    def _convert_to_input(self, message: ChatMessage) -> EvaluationInput:
        """Convert a ChatMessage to EvaluationInput.
        
        Args:
            message: ChatMessage record to convert.
        
        Returns:
            EvaluationInput object ready for evaluation.
        """
        # Extract contexts from context_document
        retrieved_contexts = []
        if message.context_document:
            # context_document is a dict with 'documents' key
            # Each document has 'content' field
            documents = message.context_document.get("documents", [])
            retrieved_contexts = [
                doc.get("content", "") 
                for doc in documents 
                if doc.get("content")
            ]
        
        # Get company_id from the associated chat
        company_id = None
        if message.chat and hasattr(message.chat, 'company_id'):
            company_id = message.chat.company_id
        
        return EvaluationInput(
            question=message.chat_query,
            retrieved_contexts=retrieved_contexts,
            answer=message.response or "",
            chat_message_id=message.id,
            company_id=company_id,
            metadata={
                "chat_id": str(message.chat_id),
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "status": message.status,
            }
        )
    
    def validate_input(self, input_data: EvaluationInput) -> List[str]:
        """Validate an EvaluationInput for evaluation.
        
        Args:
            input_data: EvaluationInput to validate.
        
        Returns:
            List of validation errors. Empty if valid.
        """
        errors = []
        
        if not input_data.question or not input_data.question.strip():
            errors.append("Question cannot be empty")
        
        if not input_data.answer or not input_data.answer.strip():
            errors.append("Answer cannot be empty")
        
        if not input_data.retrieved_contexts:
            errors.append("Retrieved contexts cannot be empty")
        
        return errors
