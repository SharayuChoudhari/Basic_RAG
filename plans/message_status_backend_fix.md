# Message Status Field Implementation Plan

## Overview

Add a `status` field to the `chat_messages` table to track message processing state. This allows the frontend to display user messages immediately with a "processing" status, then update to "done" when the response is ready.

---

## Database Schema Changes

### Step 1: Add Status Field to ChatMessage Model

**File:** [`layers/models.py`](layers/models.py)

Add `status` field to `ChatMessage` model:

```python
class ChatMessage(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    chat_id: UUID = Field(foreign_key="chat.id", nullable=False)
    chat_query: str = Field(nullable=False)
    context_document: Optional[dict] = Field(default=None, nullable=True)
    response: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    
    # NEW: Status field to track message processing state
    status: str = Field(default="processing", nullable=False)  # "processing" | "done" | "error"
```

### Step 2: Create Migration

**Command:** Generate Alembic migration

```bash
alembic revision --autogenerate -m "Add status field to chat_messages"
```

This will create a migration file in `alembic/versions/` that adds the `status` column.

---

## Backend Implementation Changes

### Step 3: Update ChatMessageService

**File:** [`services/chat_messages.py`](services/chat_messages.py)

Modify the `process_query` method to:

1. Create message with `status='processing'` and `response=None` immediately
2. Update message to `status='done'` and set `response` when complete

```python
async def process_query(self, query_request: ChatQueryRequest) -> ChatQueryResponse:
    """
    Process a chat query using LangGraph workflow with retrieval and LLM generation.
    """
    try:
        # Get conversation context
        context = await self.get_conversation_context(
            chat_id=query_request.chat_id,
            max_history=query_request.max_history
        )
        
        # Get retrieval context
        retrieval_context = await self.get_retrieval_context(
            chat_id=query_request.chat_id,
            top_k=query_request.top_k,
            use_retrieval=query_request.use_retrieval
        )
        
        # Create message with processing status immediately
        new_message = ChatMessage(
            chat_id=query_request.chat_id,
            chat_query=query_request.query,
            context_document={"documents": retrieval_context} if retrieval_context else None,
            response=None,  # Will be updated later
            status="processing",  # NEW: Set initial status
            created_at=get_current_utc_time()
        )
        self.session.add(new_message)
        self.session.commit()
        self.session.refresh(new_message)
        
        # Generate LLM response
        result = await self.generate_response(
            query=query_request.query,
            context=context,
            retrieval_context=retrieval_context,
            llm_model=query_request.llm_model,
            llm_provider=query_request.llm_provider
        )
        
        # Update message with response and done status
        new_message.response = result["response"]
        new_message.status = "done"  # NEW: Update status
        self.session.add(new_message)
        self.session.commit()
        self.session.refresh(new_message)
        
        return ChatQueryResponse(
            message_id=new_message.id,
            chat_id=new_message.chat_id,
            query=query_request.query,
            response=result["response"],
            context_documents=retrieval_context,
            created_at=new_message.created_at.isoformat(),
            llm_model=query_request.llm_model or "default",
            llm_provider=query_request.llm_provider or "default"
        )
    except Exception as e:
        # Update message with error status if generation fails
        if 'new_message' in locals():
            new_message.status = "error"
            self.session.add(new_message)
            self.session.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )
```

---

## Frontend Implementation Changes

### Step 4: Update API Types

**File:** [`frontend/types/api.ts`](frontend/types/api.ts)

Add `status` field to `ChatMessage` interface:

```typescript
export interface ChatMessage {
  id: string;
  chat_id: string;
  chat_query: string;
  context_document: Record<string, any> | null;
  response: string | null;
  created_at: string;
  status?: string;  // NEW: "processing" | "done" | "error"
}
```

### Step 5: Update ChatMessage Component

**File:** [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx)

Add visual indicator for processing status:

```typescript
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = !message.response;
  const isProcessing = message.status === 'processing';
  const isError = message.status === 'error';
  
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`flex-shrink-0 ${isUser ? 'order-2' : ''}`}>
          {isUser ? (
            <Avatar className="w-8 h-8" />
          ) : (
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
          )}
        </div>
        <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
          <div className={`rounded-lg p-4 ${
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
          }`}>
            {isProcessing && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <div className="animate-spin w-4 h-4">
                  <Loader2 className="w-full h-full" />
                </div>
                <span>Processing...</span>
              </div>
            )}
            {isError && (
              <div className="text-destructive">
                Failed to generate response. Please try again.
              </div>
            )}
            {!isProcessing && !isError && (
              <p className="whitespace-pre-wrap">
                {message.chat_query}
              </p>
            )}
            {!isProcessing && !isError && message.response && (
              <div className="mt-2">
                <p className="whitespace-pre-wrap">{message.response}</p>
                {message.context_document?.documents && 
                  message.context_document.documents.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold mb-2">References</h4>
                    <div className="space-y-2">
                      {message.context_document.documents.map((doc, idx) => (
                        <ReferenceCard key={idx} document={doc} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Step 6: Update useMessages Hook

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

Remove the temporary user message logic since backend now handles it:

```typescript
const sendMessage = async (userId: string, query: string, onFirstMessage?: (query: string) => void) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
    const isFirstMessage = messages.length === 0;
    
    const response = await sendQuery(userId, chatId, query);
    
    // Add message with both query and response (backend now handles status)
    const newMessage: ChatMessage = {
      id: response.message_id,
      chat_id: response.chat_id,
      chat_query: response.query,
      context_document: { documents: response.context_documents },
      response: response.response,
      created_at: response.created_at,
      status: 'done',  // Backend sets this
    };
    setMessages((prev) => [...prev, newMessage]);
    
    // If this was the first message, trigger auto-rename callback
    if (isFirstMessage && onFirstMessage) {
      onFirstMessage(query);
    }
    
    return response;
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send message');
    throw err;
  } finally {
    setSending(false);
  }
};
```

---

## Implementation Steps

1. **Add status field to ChatMessage model** ([`layers/models.py`](layers/models.py))
2. **Generate and run Alembic migration**
3. **Update ChatMessageService** ([`services/chat_messages.py`](services/chat_messages.py))
4. **Update frontend types** ([`frontend/types/api.ts`](frontend/types/api.ts))
5. **Update ChatMessage component** ([`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx))
6. **Update useMessages hook** ([`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts))

---

## Testing Checklist

### Backend
- [ ] Migration runs successfully
- [ ] Message is created with `status='processing'`
- [ ] Message is updated to `status='done'` after response
- [ ] Message is updated to `status='error'` on failure
- [ ] API returns correct status in response

### Frontend
- [ ] User message appears immediately with "Processing..." indicator
- [ ] Processing indicator shows while waiting for response
- [ ] Response appears when status changes to "done"
- [ ] Error message appears if status is "error"
- [ ] Auto-rename still works with first message

---

## Benefits of This Approach

1. **Backend-only solution** - No frontend state management complexity
2. **Persistent status** - Status is stored in database
3. **Page refresh support** - Status persists across page reloads
4. **Error handling** - Can track failed message generations
5. **Simple frontend** - Just display status, don't manage state transitions

---

## Files to Modify

1. [`layers/models.py`](layers/models.py) - Add status field
2. `alembic/versions/` - New migration file
3. [`services/chat_messages.py`](services/chat_messages.py) - Update process_query method
4. [`frontend/types/api.ts`](frontend/types/api.ts) - Add status to interface
5. [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx) - Add processing indicator
6. [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Simplify sendMessage logic

---

## Notes

- This approach is cleaner than the frontend-only solution
- The status field can be extended later (e.g., "streaming", "cancelled")
- Consider adding an `error_message` field for detailed error information
- The migration should be tested on a development database first
