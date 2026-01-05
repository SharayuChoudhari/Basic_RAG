from typing import List, Optional
from sqlmodel import Session, select
from layers.models import Prompt, User


class PromptDAO:
    """Data Access Object for Prompt operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Create a new prompt."""
        self.session.add(prompt)
        self.session.commit()
        self.session.refresh(prompt)
        return prompt
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Prompt]:
        """Get a prompt by ID."""
        statement = select(Prompt).where(Prompt.id == prompt_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_prompts(self) -> List[Prompt]:
        """Get all prompts."""
        statement = select(Prompt)
        result = self.session.exec(statement)
        return result.all()
    
    def get_prompts_by_user(self, user_id: int) -> List[Prompt]:
        """Get all prompts for a specific user."""
        statement = select(Prompt).where(Prompt.user_id == user_id)
        result = self.session.exec(statement)
        return result.all()
    
    def update_prompt(self, prompt: Prompt) -> Prompt:
        """Update an existing prompt."""
        self.session.add(prompt)
        self.session.commit()
        self.session.refresh(prompt)
        return prompt
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a prompt by ID."""
        prompt = self.get_prompt_by_id(prompt_id)
        if prompt:
            self.session.delete(prompt)
            self.session.commit()
            return True
        return False
    
    def get_prompt_with_user(self, prompt_id: int) -> Optional[Prompt]:
        """Get a prompt with its user information."""
        statement = select(Prompt).where(Prompt.id == prompt_id)
        result = self.session.exec(statement)
        prompt = result.first()
        # Access user to load the relationship
        if prompt:
            _ = prompt.user
        return prompt