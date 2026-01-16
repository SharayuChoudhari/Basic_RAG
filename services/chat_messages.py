from typing import List, Optional, Dict, Any, TypedDict, Annotated
from uuid import UUID
from sqlmodel import Session
from datetime import datetime

from layers.dao import ChatMessageDAO, ChatDAO, DocumentVectorDAO, CompanyDAO
from layers.models import ChatMessage, Chat, DocumentVector
from layers.schemas import (
    ChatMessageCreate, ChatMessageUpdate, ChatMessageResponse, 
    ChatMessageListResponse, ChatQueryRequest, ChatQueryResponse
)
from layers.common import get_current_utc_time

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# LLM Provider imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import HuggingFaceHub
import os


# Define the state for LangGraph
class ChatState(TypedDict):
    """State for the chat workflow."""
    query: str
    context: List[Dict[str, Any]]
    response: str
    llm_model: str
    llm_provider: str
    messages: Annotated[List[BaseMessage], "messages"]


class ChatMessageService:
    """Service layer for ChatMessage operations with LangGraph integration."""
    
    def __init__(self, session: Session):
        self.session = session
        self.chat_message_dao = ChatMessageDAO(session)
        self.chat_dao = ChatDAO(session)
        self.document_vector_dao = DocumentVectorDAO(session)
        self.company_dao = CompanyDAO(session)
        
        # Initialize LangGraph workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for chat processing."""
        
        # Define nodes
        async def retrieve_node(state: ChatState) -> ChatState:
            """Retrieve relevant documents based on the query."""
            # This will be implemented with actual retrieval logic
            # For now, return empty context
            state["context"] = []
            return state
        
        async def generate_node(state: ChatState) -> ChatState:
            """Generate response using the LLM."""
            llm = self._get_llm(state["llm_provider"], state["llm_model"])
            
            # Create prompt with context
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Use the following context to answer the user's question."),
                ("human", "{context}\n\nQuestion: {query}")
            ])
            
            # Format context
            context_text = "\n\n".join([
                f"Document {i+1}: {doc.get('content', '')}"
                for i, doc in enumerate(state["context"])
            ])
            
            # Generate response
            chain = prompt | llm | StrOutputParser()
            response = chain.invoke({
                "context": context_text if context_text else "No context available.",
                "query": state["query"]
            })
            
            state["response"] = response
            return state
        
        # Build the graph
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("generate", generate_node)
        
        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _get_llm(self, provider: str, model: str):
        """Get the LLM instance based on provider and model."""
        provider = provider.lower() if provider else "openai"
        
        if provider == "openai":
            return ChatOpenAI(
                model=model or "gpt-4",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model or "claude-3-sonnet-20240229",
                temperature=0.7,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=model or "gemini-pro",
                temperature=0.7,
                api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif provider == "huggingface":
            return HuggingFaceHub(
                repo_id=model or "google/flan-t5-large",
                huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
            )
        else:
            # Default to OpenAI
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )
    
    def _retrieve_documents(
        self, 
        query: str, 
        user_id: UUID, 
        company_id: Optional[UUID] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using vector similarity search.
        
        Args:
            query: The user's query
            user_id: ID of the user
            company_id: Optional ID of the company
            top_k: Number of top results to retrieve
            
        Returns:
            List of relevant documents with metadata
        """
        # Get embedding model from company if available
        embedding_model = "all-MiniLM-L6-v2"
        embedding_type = "local"
        
        if company_id:
            model_info = self.company_dao.get_embedding_model(company_id)
            if model_info:
                embedding_model, embedding_type = model_info
        
        # Import vectorizer for embedding generation
        from services.vectorizer import Vectorizer
        vectorizer = Vectorizer(embedding_model=embedding_model, embedding_type=embedding_type)
        
        # Generate query embedding
        query_embedding = vectorizer.embed_text(query)
        
        # Search for similar documents
        # This is a simplified version - in production, you'd use proper vector similarity search
        # For now, we'll get documents by user/company
        documents = []
        
        # Get documents for the user
        statement = select(DocumentVector).where(DocumentVector.user_id == user_id)
        if company_id:
            statement = statement.where(DocumentVector.company_id == company_id)
        
        result = self.session.exec(statement)
        all_docs = result.all()
        
        # Simple similarity calculation (in production, use pgvector similarity search)
        for doc in all_docs[:top_k]:
            documents.append({
                "document_id": doc.document_id,
                "chunk_index": doc.chunk_index,
                "content": doc.content,
                "metadata": doc.meta_data
            })
        
        return documents
    
    async def process_query(
        self, 
        query_request: ChatQueryRequest
    ) -> ChatQueryResponse:
        """
        Process a chat query using LangGraph workflow.
        
        Args:
            query_request: Query request with chat_id, query, and options
            
        Returns:
            Query response with message details
            
        Raises:
            ValueError: If chat_id or query is not provided, or chat doesn't exist
        """
        if not query_request.chat_id:
            raise ValueError("chat_id is required")
        
        if not query_request.query or not query_request.query.strip():
            raise ValueError("query is required and cannot be empty")
        
        # Get chat details
        chat = self.chat_dao.get_chat_by_id(query_request.chat_id)
        if not chat:
            raise ValueError(f"Chat with ID {query_request.chat_id} not found")
        
        # Determine LLM model and provider
        llm_model = query_request.llm_model
        llm_provider = query_request.llm_provider
        
        # If not specified, get from company settings
        if not llm_model or not llm_provider:
            if chat.company_id:
                model_info = self.company_dao.get_embedding_model(chat.company_id)
                if model_info:
                    # Use embedding_type as a proxy for LLM provider
                    llm_provider = llm_provider or model_info[1]
                    llm_model = llm_model or model_info[0]
        
        # Default values
        llm_provider = llm_provider or "openai"
        llm_model = llm_model or "gpt-4"
        
        # Retrieve documents if requested
        context_documents = []
        if query_request.use_retrieval:
            context_documents = self._retrieve_documents(
                query=query_request.query,
                user_id=chat.user_id,
                company_id=chat.company_id,
                top_k=query_request.top_k
            )
        
        # Create state for LangGraph
        state = ChatState(
            query=query_request.query,
            context=context_documents,
            response="",
            llm_model=llm_model,
            llm_provider=llm_provider,
            messages=[]
        )
        
        # Run the workflow
        result = await self.workflow.ainvoke(state)
        
        # Create chat message
        new_message = ChatMessage(
            chat_id=query_request.chat_id,
            chat_query=query_request.query,
            context_document={"documents": context_documents} if context_documents else None,
            response=result["response"],
            created_at=get_current_utc_time()
        )
        
        # Save to database
        created_message = self.chat_message_dao.create_chat_message(new_message)
        
        # Return response
        return ChatQueryResponse(
            message_id=created_message.id,
            chat_id=created_message.chat_id,
            query=created_message.chat_query,
            response=created_message.response or "",
            context_documents=context_documents,
            created_at=created_message.created_at.isoformat(),
            llm_model=llm_model,
            llm_provider=llm_provider
        )
    
    def create_chat_message(self, message_data: ChatMessageCreate) -> ChatMessageResponse:
        """
        Create a new chat message.
        
        Args:
            message_data: Chat message creation data
            
        Returns:
            Created chat message response
            
        Raises:
            ValueError: If chat_id or chat_query is not provided, or chat doesn't exist
        """
        if not message_data.chat_id:
            raise ValueError("chat_id is required to create a chat message")
        
        if not message_data.chat_query or not message_data.chat_query.strip():
            raise ValueError("chat_query is required and cannot be empty")
        
        # Check if chat exists
        chat = self.chat_dao.get_chat_by_id(message_data.chat_id)
        if not chat:
            raise ValueError(f"Chat with ID {message_data.chat_id} not found")
        
        # Create new message instance
        new_message = ChatMessage(
            chat_id=message_data.chat_id,
            chat_query=message_data.chat_query.strip(),
            context_document=message_data.context_document,
            response=message_data.response,
            created_at=get_current_utc_time()
        )
        
        # Save to database
        created_message = self.chat_message_dao.create_chat_message(new_message)
        
        # Return response
        return ChatMessageResponse(
            id=created_message.id,
            chat_id=created_message.chat_id,
            chat_query=created_message.chat_query,
            context_document=created_message.context_document,
            response=created_message.response,
            created_at=created_message.created_at.isoformat()
        )
    
    def get_message_by_id(self, message_id: UUID) -> ChatMessageResponse:
        """
        Get a chat message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Chat message response
            
        Raises:
            ValueError: If message_id is not provided or message doesn't exist
        """
        if not message_id:
            raise ValueError("message_id is required to get a message")
        
        message = self.chat_message_dao.get_chat_message_by_id(message_id)
        
        if not message:
            raise ValueError(f"Chat message with ID {message_id} not found")
        
        return ChatMessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            chat_query=message.chat_query,
            context_document=message.context_document,
            response=message.response,
            created_at=message.created_at.isoformat()
        )
    
    def get_messages_by_chat(self, chat_id: UUID) -> ChatMessageListResponse:
        """
        Get all messages for a specific chat.
        
        Args:
            chat_id: ID of the chat
            
        Returns:
            List of messages for the chat
            
        Raises:
            ValueError: If chat_id is not provided
        """
        if not chat_id:
            raise ValueError("chat_id is required to get messages")
        
        messages = self.chat_message_dao.get_messages_by_chat_ordered(chat_id)
        
        return ChatMessageListResponse(
            messages=[
                ChatMessageResponse(
                    id=msg.id,
                    chat_id=msg.chat_id,
                    chat_query=msg.chat_query,
                    context_document=msg.context_document,
                    response=msg.response,
                    created_at=msg.created_at.isoformat()
                )
                for msg in messages
            ],
            total=len(messages)
        )
    
    def update_message(self, message_id: UUID, message_update: ChatMessageUpdate) -> ChatMessageResponse:
        """
        Update a chat message.
        
        Args:
            message_id: ID of the message to update
            message_update: Message update data
            
        Returns:
            Updated chat message response
            
        Raises:
            ValueError: If message_id is not provided or message doesn't exist
        """
        if not message_id:
            raise ValueError("message_id is required to update a message")
        
        message = self.chat_message_dao.get_chat_message_by_id(message_id)
        
        if not message:
            raise ValueError(f"Chat message with ID {message_id} not found")
        
        # Update fields if provided
        if message_update.chat_query is not None:
            message.chat_query = message_update.chat_query
        if message_update.context_document is not None:
            message.context_document = message_update.context_document
        if message_update.response is not None:
            message.response = message_update.response
        
        # Save to database
        updated_message = self.chat_message_dao.update_chat_message(message)
        
        return ChatMessageResponse(
            id=updated_message.id,
            chat_id=updated_message.chat_id,
            chat_query=updated_message.chat_query,
            context_document=updated_message.context_document,
            response=updated_message.response,
            created_at=updated_message.created_at.isoformat()
        )
    
    def delete_message(self, message_id: UUID) -> bool:
        """
        Delete a chat message.
        
        Args:
            message_id: ID of the message to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            ValueError: If message_id is not provided or message doesn't exist
        """
        if not message_id:
            raise ValueError("message_id is required to delete a message")
        
        # Check if message exists
        message = self.chat_message_dao.get_chat_message_by_id(message_id)
        if not message:
            raise ValueError(f"Chat message with ID {message_id} not found")
        
        # Delete the message
        success = self.chat_message_dao.delete_chat_message(message_id)
        
        return success
    
    def delete_messages_by_chat(self, chat_id: UUID) -> int:
        """
        Delete all messages for a specific chat.
        
        Args:
            chat_id: ID of the chat
            
        Returns:
            Number of messages deleted
            
        Raises:
            ValueError: If chat_id is not provided
        """
        if not chat_id:
            raise ValueError("chat_id is required to delete messages")
        
        count = self.chat_message_dao.delete_messages_by_chat(chat_id)
        
        return count
