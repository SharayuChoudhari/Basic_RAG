# File Selection Feature for Chat Sessions

## Overview

Implement a feature where users can select specific files to use for retrieval when creating a new chat session. Users can select multiple files, all files, or a single file. Empty selection means all files should be searched.

## Requirements

### Frontend Requirements
1. Button to show available files for the company
2. User can select multiple files, all files, or a single file
3. Selection happens when creating a new chat session
4. Visual feedback for selected files

### Backend Requirements
1. New endpoint to get available documents for a company
2. Modify chat creation to accept selected document IDs
3. Modify chat query to filter retrieval by selected documents
4. Changes to SQL models to store selected documents for a chat session
5. Empty/null selection means all documents should be searched

## Current Structure Analysis

### Database Models

**Chat Model** ([`layers/models.py:85-101`](layers/models.py:85-101)):
```python
class Chat(SQLModel, table=True):
    __tablename__ = "chats"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(default_factory=get_current_utc_time)
    
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat")
```

**DocumentVector Model** ([`layers/models.py:67-82`](layers/models.py:67-82)):
```python
class DocumentVector(SQLModel, table=True):
    __tablename__ = "document_vectors"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    content: str
    embedding: List[float] = Field(sa_column=Column(Vector()))
    meta_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    document_id: UUID = Field(index=True)  # Groups chunks by document
    chunk_index: int = Field(default=0)
    user_id: UUID = Field(default_factory=uuid4, index=True)
    company_id: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=get_current_utc_time)
```

**Key Points:**
- Documents are identified by `document_id` in `DocumentVector` table
- Each document has multiple chunks (vectors) with the same `document_id`
- Document metadata (filename, etc.) is stored in `meta_data` field

## Implementation Plan

### Step 1: Database Schema Changes

**File:** [`layers/models.py`](layers/models.py)

**Add field to Chat model:**

```python
class Chat(SQLModel, table=True):
    __tablename__ = "chats"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    
    # NEW: Selected document IDs for this chat (null/empty means all documents)
    selected_document_ids: Optional[List[UUID]] = Field(
        default=None,
        sa_column=Column(JSONB),
        index=True
    )
    
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(default_factory=get_current_utc_time)
    
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat")
```

**Create Alembic Migration:**

```bash
alembic revision --autogenerate -m "add_selected_document_ids_to_chats"
```

### Step 2: Schema Updates

**File:** [`layers/schemas.py`](layers/schemas.py)

**Update ChatCreate schema:**

```python
class ChatCreate(BaseModel):
    """Schema for creating a chat."""
    title: Optional[str] = None
    user_id: UUID
    company_id: Optional[UUID] = None
    # NEW: Optional list of document IDs to use for retrieval
    selected_document_ids: Optional[List[UUID]] = None
```

**Update ChatResponse schema:**

```python
class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: UUID
    title: Optional[str] = None
    user_id: UUID
    company_id: Optional[UUID] = None
    # NEW: Selected document IDs
    selected_document_ids: Optional[List[UUID]] = None
    created_at: str
    updated_at: str
```

**Add new schema for document list:**

```python
class DocumentInfo(BaseModel):
    """Schema for document information."""
    document_id: UUID
    filename: str
    num_chunks: int
    created_at: str
    metadata: Optional[dict] = None

class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentInfo]
    total: int
```

**Update ChatQueryRequest schema:**

```python
class ChatQueryRequest(BaseModel):
    """Schema for chat query request."""
    chat_id: UUID
    query: str
    use_retrieval: bool = True
    top_k: int = 5
    llm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    max_history: int = 10
    # Note: selected_document_ids will be fetched from chat, not passed in query
```

### Step 3: DAO Layer Updates

**File:** [`layers/dao/document_vectors_dao.py`](layers/dao/document_vectors_dao.py)

**Add method to get unique documents for a company:**

```python
def get_unique_documents_by_company(self, company_id: UUID) -> List[Dict[str, Any]]:
    """Get unique documents for a company with their metadata."""
    from sqlalchemy import func
    
    # Group by document_id and get first chunk's metadata
    statement = (
        select(
            DocumentVector.document_id,
            func.min(DocumentVector.created_at).label('created_at'),
            func.count(DocumentVector.id).label('num_chunks')
        )
        .where(DocumentVector.company_id == company_id)
        .group_by(DocumentVector.document_id)
        .order_by(func.min(DocumentVector.created_at).desc())
    )
    
    result = self.session.exec(statement)
    documents = []
    
    for row in result:
        # Get metadata from first chunk
        first_chunk = (
            select(DocumentVector)
            .where(
                DocumentVector.document_id == row.document_id,
                DocumentVector.company_id == company_id
            )
            .order_by(DocumentVector.chunk_index)
            .limit(1)
        )
        chunk_result = self.session.exec(first_chunk).first()
        
        if chunk_result and chunk_result.meta_data:
            filename = chunk_result.meta_data.get('filename', 'Unknown')
            metadata = chunk_result.meta_data
        else:
            filename = 'Unknown'
            metadata = None
        
        documents.append({
            'document_id': row.document_id,
            'filename': filename,
            'num_chunks': row.num_chunks,
            'created_at': row.created_at.isoformat() if row.created_at else '',
            'metadata': metadata
        })
    
    return documents
```

**Add method to get vectors by document IDs:**

```python
def get_vectors_by_document_ids(
    self, 
    document_ids: List[UUID]
) -> List[DocumentVector]:
    """Get all vectors for specific document IDs."""
    statement = select(DocumentVector).where(
        DocumentVector.document_id.in_(document_ids)
    )
    result = self.session.exec(statement)
    return result.all()
```

### Step 4: Service Layer Updates

**File:** [`services/chat_messages.py`](services/chat_messages.py)

**Modify `_retrieve_documents` method to filter by selected documents:**

```python
def _retrieve_documents(
    self, 
    query: str, 
    user_id: UUID, 
    company_id: Optional[UUID] = None,
    selected_document_ids: Optional[List[UUID]] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant documents using vector similarity search.
    
    Args:
        query: The user's query
        user_id: ID of the user
        company_id: Optional ID of the company
        selected_document_ids: Optional list of document IDs to filter by
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
    from services.vectorizer import VectorizerFactory
    vectorizer = VectorizerFactory.create_vectorizer(
        vectorizer_type=embedding_type,
        model=embedding_model
    )
    
    # Generate query embedding
    query_embedding = vectorizer.embed(query)
    
    # Get documents for the user/company
    if selected_document_ids:
        # Filter by selected document IDs
        statement = select(DocumentVector).where(
            DocumentVector.user_id == user_id,
            DocumentVector.document_id.in_(selected_document_ids)
        )
        if company_id:
            statement = statement.where(DocumentVector.company_id == company_id)
    else:
        # Get all documents for the user/company
        statement = select(DocumentVector).where(DocumentVector.user_id == user_id)
        if company_id:
            statement = statement.where(DocumentVector.company_id == company_id)
    
    result = self.session.exec(statement)
    all_docs = result.all()
    
    # Calculate cosine similarity for each document
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    doc_similarities = []
    for doc in all_docs:
        # Check if embedding exists and is not empty
        if doc.embedding is not None and len(doc.embedding) > 0:
            # Convert embedding to numpy array if needed
            doc_embedding = np.array(doc.embedding).reshape(1, -1)
            query_emb_array = np.array(query_embedding).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_emb_array, doc_embedding)[0][0]
            
            doc_similarities.append({
                "document_id": str(doc.document_id),
                "chunk_index": doc.chunk_index,
                "content": doc.content,
                "metadata": doc.meta_data,
                "similarity": similarity
            })
    
    # Sort by similarity score (descending) and return top_k
    doc_similarities.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top_k documents
    return doc_similarities[:top_k]
```

**Modify `process_query` method to use selected documents:**

```python
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
    
    # Get selected document IDs from chat
    selected_document_ids = getattr(chat, 'selected_document_ids', None)
    
    # Determine LLM model and provider
    llm_model = query_request.llm_model
    llm_provider = query_request.llm_provider
    llm_config = {}
    
    # If not specified, get from company settings
    if not llm_model or not llm_provider:
        if chat.company_id:
            llm_config = self.company_dao.get_llm_config(chat.company_id)
            if llm_config:
                llm_provider = llm_provider or llm_config.get("llm_provider", "openai")
                llm_model = llm_model or llm_config.get("llm_model", "gpt-4")
    
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
            selected_document_ids=selected_document_ids,  # Pass selected documents
            top_k=query_request.top_k
        )
    
    # ... rest of the method remains the same
```

### Step 5: Controller Updates

**File:** [`controllers/chat.py`](controllers/chat.py)

**Update create_chat endpoint:**

```python
@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new chat session.
    
    Args:
        chat_data: Chat creation data including title, user_id, company_id, and selected_document_ids
        session: Database session
        
    Returns:
        Created chat response
    """
    try:
        chat_service = ChatService(session)
        created_chat = chat_service.create_chat(chat_data)
        return created_chat
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat: {str(e)}"
        )
```

**Add new endpoint to get documents for a company:**

```python
@router.get("/documents/company/{company_id}", response_model=DocumentListResponse)
async def get_documents_by_company(
    company_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Get all unique documents for a specific company.
    
    Args:
        company_id: ID of the company
        session: Database session
        
    Returns:
        List of documents with metadata
    """
    try:
        document_vector_dao = DocumentVectorDAO(session)
        documents = document_vector_dao.get_unique_documents_by_company(company_id)
        
        return DocumentListResponse(
            documents=[
                DocumentInfo(
                    document_id=doc['document_id'],
                    filename=doc['filename'],
                    num_chunks=doc['num_chunks'],
                    created_at=doc['created_at'],
                    metadata=doc['metadata']
                )
                for doc in documents
            ],
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )
```

**Update rename_chat endpoint to preserve selected_document_ids:**

```python
@router.put("/{chat_id}/rename", response_model=ChatResponse)
async def rename_chat(
    chat_id: UUID,
    new_title: str,
    session: Session = Depends(get_db_session)
):
    """
    Rename a chat session.
    
    Args:
        chat_id: ID of the chat to rename
        new_title: New title for the chat
        session: Database session
        
    Returns:
        Updated chat response
    """
    try:
        chat_service = ChatService(session)
        updated_chat = chat_service.rename_chat(chat_id, new_title)
        return updated_chat
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rename chat: {str(e)}"
        )
```

### Step 6: Frontend API Layer

**File:** [`frontend/lib/api.ts`](frontend/lib/api.ts)

**Add new types:**

```typescript
// Document types
export interface DocumentInfo {
  document_id: string;
  filename: string;
  num_chunks: number;
  created_at: string;
  metadata: Record<string, any> | null;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
}

// Update Chat type
export interface Chat {
  id: string;
  title: string | null;
  user_id: string;
  company_id: string | null;
  selected_document_ids: string[] | null;  // NEW
  created_at: string;
  updated_at: string;
}
```

**Add new API functions:**

```typescript
// Documents
export async function fetchDocumentsByCompany(companyId: string): Promise<DocumentListResponse> {
  const response = await fetch(`${API_BASE_URL}/chats/documents/company/${companyId}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to fetch documents');
  return response.json();
}

// Update createChat to accept selected documents
export async function createChat(
  userId: string,
  title?: string,
  companyId?: string,
  selectedDocumentIds?: string[]
): Promise<Chat> {
  const body: { 
    user_id: string; 
    title?: string; 
    company_id?: string;
    selected_document_ids?: string[];
  } = { user_id: userId };
  
  if (title) body.title = title;
  if (companyId) body.company_id = companyId;
  if (selectedDocumentIds) body.selected_document_ids = selectedDocumentIds;
  
  const response = await fetch(`${API_BASE_URL}/chats`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error('Failed to create chat');
  return response.json();
}
```

### Step 7: Frontend Hook Updates

**File:** [`frontend/hooks/useChats.ts`](frontend/hooks/useChats.ts)

**Update createNewChat to accept selected documents:**

```typescript
const createNewChat = async (
  title?: string, 
  companyId?: string,
  selectedDocumentIds?: string[]
) => {
  if (!userId) throw new Error('No user selected');
  const newChat = await createChat(userId, title, companyId, selectedDocumentIds);
  setChats((prev) => [newChat, ...prev]);
  return newChat;
};
```

**Add new hook for documents:**

```typescript
// frontend/hooks/useDocuments.ts
import { useState, useEffect } from 'react';
import { fetchDocumentsByCompany } from '@/lib/api';
import { DocumentInfo } from '@/types/api';

export function useDocuments(companyId: string | null) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    if (!companyId) return;
    setLoading(true);
    try {
      const data = await fetchDocumentsByCompany(companyId);
      setDocuments(data.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [companyId]);

  return { documents, loading, error, refresh };
}
```

### Step 8: Frontend Component - DocumentSelector

**Create new file:** [`frontend/components/DocumentSelector.tsx`](frontend/components/DocumentSelector.tsx)

```typescript
'use client';

import { useState } from 'react';
import { DocumentInfo } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Check, X } from 'lucide-react';

interface DocumentSelectorProps {
  documents: DocumentInfo[];
  selectedDocumentIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onClose: () => void;
}

export function DocumentSelector({
  documents,
  selectedDocumentIds,
  onSelectionChange,
  onClose,
}: DocumentSelectorProps) {
  const [selectAll, setSelectAll] = useState(false);

  const handleToggleDocument = (documentId: string) => {
    if (selectedDocumentIds.includes(documentId)) {
      onSelectionChange(selectedDocumentIds.filter(id => id !== documentId));
    } else {
      onSelectionChange([...selectedDocumentIds, documentId]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      onSelectionChange([]);
      setSelectAll(false);
    } else {
      onSelectionChange(documents.map(doc => doc.document_id));
      setSelectAll(true);
    }
  };

  const selectedCount = selectedDocumentIds.length;
  const totalCount = documents.length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">Select Documents</h2>
            <p className="text-sm text-muted-foreground">
              {selectedCount} of {totalCount} documents selected
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Select All Button */}
        <div className="p-4 border-b">
          <Button
            variant="outline"
            onClick={handleSelectAll}
            className="w-full"
          >
            {selectAll ? (
              <>
                <X className="w-4 h-4 mr-2" />
                Deselect All
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Select All ({totalCount})
              </>
            )}
          </Button>
        </div>

        {/* Document List */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-2">
            {documents.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No documents available. Upload some documents first.
              </div>
            ) : (
              documents.map((document) => (
                <div
                  key={document.document_id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDocumentIds.includes(document.document_id)
                      ? 'bg-primary/10 border-primary'
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => handleToggleDocument(document.document_id)}
                >
                  <Checkbox
                    checked={selectedDocumentIds.includes(document.document_id)}
                    onChange={() => handleToggleDocument(document.document_id)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-medium truncate">
                        {document.filename}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {document.num_chunks} chunks • {new Date(document.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t flex justify-between items-center">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onClose}>
            Done ({selectedCount} selected)
          </Button>
        </div>
      </div>
    </div>
  );
}
```

### Step 9: Frontend Component - ChatSidebar Updates

**File:** [`frontend/components/ChatSidebar.tsx`](frontend/components/ChatSidebar.tsx)

**Add document selector button and state:**

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Trash2, Plus, FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Chat } from '@/types/api';
import { DocumentSelector } from './DocumentSelector';

interface ChatSidebarProps {
  selectedChatId: string | null;
  chats: Chat[];
  documents: any[];  // NEW
  onSelectChat: (chatId: string) => void;
  onNewChat: (selectedDocumentIds?: string[]) => void;  // UPDATED
  onDeleteChat: (chatId: string) => void;
}

export function ChatSidebar({
  selectedChatId,
  chats,
  documents,
  onSelectChat,
  onNewChat,
  onDeleteChat,
}: ChatSidebarProps) {
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);

  const handleNewChat = () => {
    setShowDocumentSelector(true);
    setSelectedDocumentIds([]);
  };

  const handleConfirmDocumentSelection = () => {
    onNewChat(selectedDocumentIds);
    setShowDocumentSelector(false);
    setSelectedDocumentIds([]);
  };

  return (
    <div className="w-64 border-r bg-muted/10 flex flex-col">
      <div className="p-4 border-b">
        <Button onClick={handleNewChat} className="w-full" variant="outline">
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {chats.length === 0 ? (
            <div className="text-sm text-muted-foreground p-4 text-center">
              No chats yet
            </div>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors cursor-pointer ${
                  selectedChatId === chat.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    <span className="font-medium truncate">{chat.title || 'Untitled Chat'}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 flex-shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat(chat.id);
                    }}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(chat.created_at), { addSuffix: true })}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Document Selector Modal */}
      {showDocumentSelector && (
        <DocumentSelector
          documents={documents}
          selectedDocumentIds={selectedDocumentIds}
          onSelectionChange={setSelectedDocumentIds}
          onClose={() => setShowDocumentSelector(false)}
        />
      )}
    </div>
  );
}
```

### Step 10: Frontend Page Updates

**File:** [`frontend/app/page.tsx`](frontend/app/page.tsx)

**Add document hook and pass to ChatSidebar:**

```typescript
import { useDocuments } from '@/hooks/useDocuments';

function ChatPage() {
  const { selectedCompany, selectedUser, setSelectedCompany, setSelectedUser } = useApp();
  const { setDemoUser } = useAuth();
  const { companies } = useCompanies();
  const { users } = useUsers(selectedCompany?.id);
  const { chats, createNewChat, removeChat } = useChats(selectedUser?.id || null);
  const { documents } = useDocuments(selectedCompany?.id);  // NEW
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const { messages, sendMessage, sending } = useMessages(selectedChatId);

  const handleNewChat = async (selectedDocumentIds?: string[]) => {
    const newChat = await createNewChat('New Chat', selectedCompany?.id, selectedDocumentIds);
    setSelectedChatId(newChat.id);
  };

  // ... rest of the component

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b bg-background p-4">
        <h1 className="text-2xl font-bold">RAG Chatbot</h1>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <div className="w-80 flex-shrink-0 border-r overflow-y-auto">
          <CompanyUserSelector
            selectedCompany={selectedCompany}
            selectedUser={selectedUser}
            onCompanyChange={handleCompanyChange}
            onUserChange={handleUserChange}
          />
          <div className="p-4">
            <FileUpload />
          </div>
          <ChatSidebar
            selectedChatId={selectedChatId}
            chats={chats}
            documents={documents}  // NEW
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}  // UPDATED
            onDeleteChat={removeChat}
          />
        </div>
        <ChatInterface
          chatId={selectedChatId}
          messages={messages}
          sending={sending}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
}
```

### Step 11: Add Checkbox Component

**Create new file:** [`frontend/components/ui/checkbox.tsx`](frontend/components/ui/checkbox.tsx)

```typescript
'use client';

import * as React from "react"
import * as CheckboxPrimitive from "@radix-ui/react-checkbox"
import { Check } from "lucide-react"

import { cn } from "@/lib/utils"

const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
      className
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator
      className={cn("flex items-center justify-center text-current")}
    >
      <Check className="h-4 w-4" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
))
Checkbox.displayName = CheckboxPrimitive.Root.displayName

export { Checkbox }
```

## Testing Checklist

### Backend
- [ ] Database migration created and applied successfully
- [ ] Chat model includes `selected_document_ids` field
- [ ] GET `/chats/documents/company/{company_id}` returns list of documents
- [ ] POST `/chats` accepts `selected_document_ids` parameter
- [ ] Chat query retrieval filters by selected documents
- [ ] Empty/null `selected_document_ids` searches all documents

### Frontend
- [ ] DocumentSelector component displays available documents
- [ ] User can select/deselect individual documents
- [ ] Select All button works correctly
- [ ] Deselect All button works correctly
- [ ] Selected count displays correctly
- [ ] New Chat button opens DocumentSelector
- [ ] Confirming selection creates chat with selected documents
- [ ] Chat retrieval uses only selected documents
- [ ] Empty selection searches all documents

## Files to Create/Modify

### Backend
1. [`layers/models.py`](layers/models.py) - Add `selected_document_ids` to Chat model
2. [`layers/schemas.py`](layers/schemas.py) - Update schemas
3. [`layers/dao/document_vectors_dao.py`](layers/dao/document_vectors_dao.py) - Add document query methods
4. [`services/chat_messages.py`](services/chat_messages.py) - Update retrieval logic
5. [`controllers/chat.py`](controllers/chat.py) - Add document endpoint
6. Alembic migration file

### Frontend
1. [`frontend/types/api.ts`](frontend/types/api.ts) - Add DocumentInfo type
2. [`frontend/lib/api.ts`](frontend/lib/api.ts) - Add document API functions
3. [`frontend/hooks/useDocuments.ts`](frontend/hooks/useDocuments.ts) - New hook
4. [`frontend/hooks/useChats.ts`](frontend/hooks/useChats.ts) - Update createNewChat
5. [`frontend/components/DocumentSelector.tsx`](frontend/components/DocumentSelector.tsx) - New component
6. [`frontend/components/ChatSidebar.tsx`](frontend/components/ChatSidebar.tsx) - Add document selector
7. [`frontend/components/ui/checkbox.tsx`](frontend/components/ui/checkbox.tsx) - New component
8. [`frontend/app/page.tsx`](frontend/app/page.tsx) - Integrate document selector

## Notes

- The `selected_document_ids` field stores an array of document IDs as JSONB
- Empty/null array means all documents should be searched
- Document metadata (filename, etc.) is extracted from the first chunk's `meta_data` field
- The retrieval logic filters by `document_id` to ensure only selected documents are searched
- The UI provides clear feedback on how many documents are selected
- Users can select all, none, or specific documents for each chat session
