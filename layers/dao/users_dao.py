from typing import List, Optional
from sqlmodel import Session, select
from layers.models import User, Company, Prompt


class UserDAO:
    """Data Access Object for User operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_user(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        statement = select(User).where(User.id == user_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        statement = select(User).where(User.email == email)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        statement = select(User)
        result = self.session.exec(statement)
        return result.all()
    
    def update_user(self, user: User) -> User:
        """Update an existing user."""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        user = self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    def assign_user_to_company(self, user_id: int, company_id: int) -> Optional[User]:
        """Assign a user to a company."""
        user = self.get_user_by_id(user_id)
        if user:
            user.company_id = company_id
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        return user
    
    def get_users_by_company(self, company_id: int) -> List[User]:
        """Get all users belonging to a specific company."""
        statement = select(User).where(User.company_id == company_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_user_with_prompts(self, user_id: int) -> Optional[User]:
        """Get a user with their prompts."""
        statement = select(User).where(User.id == user_id)
        result = self.session.exec(statement)
        user = result.first()
        # Access prompts to load the relationship
        if user:
            _ = user.prompts
        return user
    
    def get_user_with_company(self, user_id: int) -> Optional[User]:
        """Get a user with their company information."""
        statement = select(User).where(User.id == user_id)
        result = self.session.exec(statement)
        user = result.first()
        # Access company to load the relationship
        if user:
            _ = user.company
        return user