from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
import requests
import os


class Vectorizer(ABC):
    """Abstract base class for vectorizers."""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Convert text to embedding vector."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors."""
        pass


class OpenAIVectorizer(Vectorizer):
    """OpenAI API based vectorizer."""
    
    def __init__(self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key
    
    def embed(self, text: str) -> List[float]:
        """Convert text to embedding vector using OpenAI."""
        response = openai.Embedding.create(
            model=self.model,
            input=text
        )
        return response['data'][0]['embedding']
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors using OpenAI."""
        response = openai.Embedding.create(
            model=self.model,
            input=texts
        )
        return [item['embedding'] for item in response['data']]


class HuggingFaceVectorizer(Vectorizer):
    """HuggingFace API based vectorizer."""
    
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def embed(self, text: str) -> List[float]:
        """Convert text to embedding vector using HuggingFace."""
        payload = {"inputs": text}
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"HuggingFace API error: {response.text}")
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        elif isinstance(result, dict) and "embeddings" in result:
            return result["embeddings"][0]
        else:
            raise Exception(f"Unexpected response format from HuggingFace API: {result}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors using HuggingFace."""
        payload = {"inputs": texts}
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"HuggingFace API error: {response.text}")
        
        result = response.json()
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "embeddings" in result:
            return result["embeddings"]
        else:
            raise Exception(f"Unexpected response format from HuggingFace API: {result}")


class LocalVectorizer(Vectorizer):
    """Local vectorizer using sentence-transformers."""
    
    def __init__(self, model: str = "all-MiniLM-L6-v2", device: Optional[str] = None):
        self.model = model
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Determine device if not specified
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load model with explicit device to avoid meta tensor issues
            self.model_instance = SentenceTransformer(
                model,
                device=device
            )
            
            # Ensure model is properly initialized by running a dummy forward pass
            # This forces the model to materialize from meta tensors if needed
            try:
                with torch.no_grad():
                    _ = self.model_instance.encode(["test"], convert_to_tensor=True)
            except Exception as e:
                # If dummy forward pass fails, try to reinitialize the model
                # This handles cases where meta tensors were used during initialization
                self.model_instance = SentenceTransformer(
                    model,
                    device=device
                )
                
        except ImportError:
            raise ImportError("sentence-transformers is required for LocalVectorizer. Install with: pip install sentence-transformers")
    
    def embed(self, text: str) -> List[float]:
        """Convert text to embedding vector using local model."""
        embedding = self.model_instance.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors using local model."""
        embeddings = self.model_instance.encode(texts)
        return [embedding.tolist() for embedding in embeddings]


class VectorizerFactory:
    """Factory class to create vectorizers."""
    
    @staticmethod
    def create_vectorizer(vectorizer_type: str, **kwargs) -> Vectorizer:
        """Create a vectorizer instance based on type."""
        if vectorizer_type.lower() == "openai":
            return OpenAIVectorizer(**kwargs)
        elif vectorizer_type.lower() == "huggingface":
            return HuggingFaceVectorizer(**kwargs)
        elif vectorizer_type.lower() == "local":
            return LocalVectorizer(**kwargs)
        else:
            raise ValueError(f"Unknown vectorizer type: {vectorizer_type}")