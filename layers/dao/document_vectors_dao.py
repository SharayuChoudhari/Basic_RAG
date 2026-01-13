from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import Session, select
from layers.models import DocumentVector


class DocumentVectorDAO:
    """Data Access Object for DocumentVector operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_document_vector(self, document_vector: DocumentVector) -> DocumentVector:
        """Create a new document vector."""
        self.session.add(document_vector)
        self.session.commit()
        self.session.refresh(document_vector)
        return document_vector
    
    def get_document_vector_by_id(self, vector_id: UUID) -> Optional[DocumentVector]:
        """Get a document vector by ID."""
        statement = select(DocumentVector).where(DocumentVector.id == vector_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all_document_vectors(self) -> List[DocumentVector]:
        """Get all document vectors."""
        statement = select(DocumentVector)
        result = self.session.exec(statement)
        return result.all()
    
    def get_vectors_by_document_id(self, document_id: UUID) -> List[DocumentVector]:
        """Get all vectors for a specific document."""
        statement = select(DocumentVector).where(DocumentVector.document_id == document_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_vectors_by_document_id_ordered(self, document_id: UUID) -> List[DocumentVector]:
        """Get all vectors for a specific document ordered by chunk index."""
        statement = select(DocumentVector).where(
            DocumentVector.document_id == document_id
        ).order_by(DocumentVector.chunk_index)
        result = self.session.exec(statement)
        return result.all()
    
    def update_document_vector(self, document_vector: DocumentVector) -> DocumentVector:
        """Update an existing document vector."""
        self.session.add(document_vector)
        self.session.commit()
        self.session.refresh(document_vector)
        return document_vector
    
    def delete_document_vector(self, vector_id: UUID) -> bool:
        """Delete a document vector by ID."""
        vector = self.get_document_vector_by_id(vector_id)
        if vector:
            self.session.delete(vector)
            self.session.commit()
            return True
        return False
    
    def delete_vectors_by_document_id(self, document_id: UUID) -> bool:
        """Delete all vectors for a specific document."""
        vectors = self.get_vectors_by_document_id(document_id)
        if vectors:
            for vector in vectors:
                self.session.delete(vector)
            self.session.commit()
            return True
        return False
    
    def search_similar_vectors(self, query_embedding: List[float], limit: int = 5) -> List[DocumentVector]:
        """Search for similar vectors using cosine similarity.
        
        Note: This method requires pgvector extension and proper database setup.
        The actual implementation may vary based on your pgvector setup.
        """
        # This is a basic implementation. In a real scenario, you would use
        # pgvector's cosine distance operator (<=>) for similarity search.
        # Example SQL: SELECT * FROM document_vectors ORDER BY embedding <=> :query_embedding LIMIT :limit
        
        # For now, we'll return all vectors (placeholder implementation)
        statement = select(DocumentVector).limit(limit)
        result = self.session.exec(statement)
        return result.all()
    
    def get_vectors_by_metadata(self, metadata_key: str, metadata_value: Any) -> List[DocumentVector]:
        """Get vectors that have specific metadata key-value pair.
        
        Note: This is a basic implementation. In a real scenario, you would use
        PostgreSQL's JSONB operators for efficient metadata queries.
        """
        # This is a placeholder implementation. In a real scenario, you would:
        # 1. Query vectors where meta_data->>:metadata_key = :metadata_value
        # 2. Or use other JSONB operators depending on your needs
        
        # For now, we'll return all vectors and filter in Python (not efficient for large datasets)
        statement = select(DocumentVector)
        result = self.session.exec(statement)
        all_vectors = result.all()
        
        filtered_vectors = []
        for vector in all_vectors:
            if vector.meta_data and isinstance(vector.meta_data, dict):
                if vector.meta_data.get(metadata_key) == metadata_value:
                    filtered_vectors.append(vector)
        
        return filtered_vectors
    
    def get_vectors_by_user_id(self, user_id: UUID) -> List[DocumentVector]:
        """Get all vectors for a specific user."""
        statement = select(DocumentVector).where(DocumentVector.user_id == user_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_vectors_by_company_id(self, company_id: UUID) -> List[DocumentVector]:
        """Get all vectors for a specific company."""
        statement = select(DocumentVector).where(DocumentVector.company_id == company_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_vectors_by_user_and_company(self, user_id: UUID, company_id: UUID) -> List[DocumentVector]:
        """Get all vectors for a specific user within a company."""
        statement = select(DocumentVector).where(
            DocumentVector.user_id == user_id,
            DocumentVector.company_id == company_id
        )
        result = self.session.exec(statement)
        return result.all()