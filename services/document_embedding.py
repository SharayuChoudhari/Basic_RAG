import uuid
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlmodel import Session
from layers.models import DocumentVector
from layers.dao import DocumentVectorDAO
from services.vectorizer import Vectorizer, VectorizerFactory


class DocumentEmbeddingService:
    """Service for document embedding with chunking and vectorization."""
    
    def __init__(self, session: Session, vectorizer: Vectorizer):
        self.session = session
        self.vectorizer = vectorizer
        self.document_vector_dao = DocumentVectorDAO(session)
    
    def process_document(
        self,
        text: str,
        user_id: UUID,
        company_id: Optional[UUID] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Process a document by chunking, vectorizing, and storing embeddings.
        
        Args:
            text: The document text to process
            user_id: The ID of the user owning this document
            company_id: The ID of the company owning this document (optional)
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            metadata: Additional metadata to store with the document
            
        Returns:
            The document ID
        """
        # Generate a unique document ID
        document_id = uuid.uuid4()
        
        # Chunk the document
        chunks = self._sliding_window_chunk(text, chunk_size, overlap)
        
        # Vectorize chunks
        embeddings = self.vectorizer.embed_batch(chunks)
        
        # Store document vectors
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            document_vector = DocumentVector(
                content=chunk,
                embedding=embedding,
                meta_data=metadata or {},
                document_id=document_id,
                chunk_index=i,
                user_id=user_id,
                company_id=company_id
            )
            self.document_vector_dao.create_document_vector(document_vector)
        
        return document_id
    
    def _sliding_window_chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into chunks using sliding window with overlap.
        
        Args:
            text: The text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If we're at the beginning or the chunk ends at the end of the text
            if start == 0 or end >= len(text):
                chunk = text[start:end]
                chunks.append(chunk)
                if end >= len(text):
                    break
            else:
                # Try to break at word boundary
                chunk = text[start:end]
                # Find the last space in the chunk
                last_space = chunk.rfind(' ')
                if last_space > 0 and (end - last_space) < (chunk_size * 0.3):
                    # Adjust to break at word boundary
                    chunk = chunk[:last_space]
                    end = start + last_space
                
                chunks.append(chunk)
            
            # Move start position for next chunk
            start = end - overlap
        
        return chunks
    
    def get_document_chunks(self, document_id: UUID) -> List[DocumentVector]:
        """Get all chunks for a document."""
        return self.document_vector_dao.get_vectors_by_document_id_ordered(document_id)
    
    def delete_document(self, document_id: UUID) -> bool:
        """Delete all vectors for a document."""
        return self.document_vector_dao.delete_vectors_by_document_id(document_id)
    
    def search_similar_documents(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[Tuple[DocumentVector, float]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: The search query text
            user_id: If provided, only search within user's documents
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (DocumentVector, similarity_score)
        """
        # Vectorize the query
        query_embedding = self.vectorizer.embed(query)
        
        # Get similar vectors (placeholder implementation)
        # In a real implementation, you would use pgvector's similarity search
        similar_vectors = self.document_vector_dao.search_similar_vectors(query_embedding, limit * 2)
        
        # Filter by user_id if provided
        if user_id is not None:
            # This is a placeholder - in a real implementation, you would:
            # 1. Join with user information in the database query
            # 2. Or store user_id in the DocumentVector model
            # For now, we'll assume all documents belong to the user
            pass
        
        # Calculate similarity scores (placeholder)
        # In a real implementation, this would be done by the database
        results = []
        for vector in similar_vectors[:limit]:
            # Simple cosine similarity calculation (placeholder)
            # In production, use pgvector's built-in similarity functions
            similarity = self._calculate_cosine_similarity(query_embedding, vector.embedding)
            results.append((vector, similarity))
        
        # Sort by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        def dot_product(a, b):
            return sum(a_i * b_i for a_i, b_i in zip(a, b))
        
        def magnitude(a):
            return math.sqrt(sum(a_i * a_i for a_i in a))
        
        if not vec1 or not vec2:
            return 0.0
        
        dot = dot_product(vec1, vec2)
        mag1 = magnitude(vec1)
        mag2 = magnitude(vec2)
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot / (mag1 * mag2)
    
    def update_document_metadata(self, document_id: UUID, metadata: Dict[str, Any]) -> bool:
        """Update metadata for all chunks of a document."""
        vectors = self.document_vector_dao.get_vectors_by_document_id(document_id)
        
        for vector in vectors:
            if vector.meta_data is None:
                vector.meta_data = {}
            vector.meta_data.update(metadata)
            self.document_vector_dao.update_document_vector(vector)
        
        return len(vectors) > 0