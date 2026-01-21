from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from layers.models import Company, User


class CompanyDAO:
    """Data Access Object for Company operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_company(self, company: Company) -> Company:
        """Create a new company."""
        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)
        return company
    
    def get_company_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get a company by ID."""
        statement = select(Company).where(Company.id == company_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get a company by name."""
        statement = select(Company).where(Company.name == name)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_companies(self) -> List[Company]:
        """Get all companies."""
        statement = select(Company)
        result = self.session.exec(statement)
        return result.all()
    
    def update_company(self, company: Company) -> Company:
        """Update an existing company."""
        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)
        return company
    
    def delete_company(self, company_id: UUID) -> bool:
        """Delete a company by ID."""
        company = self.get_company_by_id(company_id)
        if company:
            self.session.delete(company)
            self.session.commit()
            return True
        return False
    
    def get_company_with_users(self, company_id: UUID) -> Optional[Company]:
        """Get a company with its users."""
        statement = select(Company).where(Company.id == company_id)
        result = self.session.exec(statement)
        company = result.first()
        # Access users to load the relationship
        if company:
            _ = company.users
        return company
    
    def update_embedding_model(self, company_id: UUID, embedding_model: str, embedding_type: str = "local") -> Optional[Company]:
        """Update the embedding model for a company."""
        company = self.get_company_by_id(company_id)
        if company:
            company.embedding_model = embedding_model
            company.embedding_type = embedding_type
            self.session.add(company)
            self.session.commit()
            self.session.refresh(company)
        return company
    
    def get_embedding_model(self, company_id: UUID) -> Optional[tuple[str, str]]:
        """Get the embedding model and type for a company."""
        company = self.get_company_by_id(company_id)
        if company:
            return (company.embedding_model, company.embedding_type)
        return None
    
    def get_llm_config(self, company_id: UUID) -> Optional[dict]:
        """Get the LLM configuration for a company."""
        company = self.get_company_by_id(company_id)
        if company:
            return {
                "llm_model": company.llm_model,
                "llm_provider": company.llm_provider,
                "llm_endpoint": company.llm_endpoint,
                "llm_api_key": company.llm_api_key,
                "llm_temperature": company.llm_temperature,
                "llm_max_tokens": company.llm_max_tokens
            }
        return None
    
    def update_llm_config(self, company_id: UUID, llm_config: dict) -> Optional[Company]:
        """Update the LLM configuration for a company."""
        company = self.get_company_by_id(company_id)
        if company:
            if "llm_model" in llm_config:
                company.llm_model = llm_config["llm_model"]
            if "llm_provider" in llm_config:
                company.llm_provider = llm_config["llm_provider"]
            if "llm_endpoint" in llm_config:
                company.llm_endpoint = llm_config["llm_endpoint"]
            if "llm_api_key" in llm_config:
                company.llm_api_key = llm_config["llm_api_key"]
            if "llm_temperature" in llm_config:
                company.llm_temperature = llm_config["llm_temperature"]
            if "llm_max_tokens" in llm_config:
                company.llm_max_tokens = llm_config["llm_max_tokens"]
            self.session.add(company)
            self.session.commit()
            self.session.refresh(company)
        return company