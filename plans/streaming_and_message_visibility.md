# Streaming Output and Message Visibility Improvements

## Issues Identified

### Issue 1: User Message Not Visible During Processing

**Current State:**
- When a user sends a query, the message is only added to the UI after the AI response is received
- The user sees no feedback that their message was sent while waiting for the response
- This creates a poor user experience with no visual confirmation

**Root Cause:**
In [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts:24-48), the `sendMessage` function:
1. First sends the query to the backend via `sendQuery()`
2. Only after receiving the response, adds the message to state
3. The user message is never added immediately to show it was sent

### Issue 2: No Streaming Output

**Current State:**
- AI responses appear all at once after the entire response is generated
- No progressive display of the response as it's being generated
- Users have to wait without any feedback during generation

**Root Cause:**
- The backend endpoint `/api/v1/chat-messages/query` returns the complete response
- No streaming mechanism is implemented
- Frontend waits for the full response before displaying anything

---

## Implementation Plan

### Step 1: Show User Message Immediately

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

**Current Implementation:**
```tsx
const sendMessage = async (userId: string, query: string, onFirstMessage?: (query: string) => void) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
    const isFirstMessage = messages.length === 0;
    
    const response = await sendQuery(userId, chatId, query);
    
    // Add message with both query and response (single data point)
    const newMessage: ChatMessage = {
      id: response.message_id,
      chat_id: response.chat_id,
      chat_query: response.query,
      context_document: { documents: response.context_documents },
      response: response.response,
      created_at: response.created_at,
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

**Solution:**
Add the user message immediately before sending the query:

```tsx
const sendMessage = async (userId: string, query: string, onFirstMessage?: (query: string) => void) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  
  // Add user message immediately to show it was sent
  const userMessage: ChatMessage = {
    id: `temp-${Date.now()}-user`,
    chat_id: chatId,
    chat_query: query,
    context_document: null,
    response: null, // This makes it display as a user message
    created_at: new Date().toISOString(),
  };
  setMessages((prev) => [...prev, userMessage]);
  
  try {
    const isFirstMessage = messages.length === 0;
    
    const response = await sendQuery(userId, chatId, query);
    
    // Add AI response as a separate message
    const aiMessage: ChatMessage = {
      id: response.message_id,
      chat_id: response.chat_id,
      chat_query: query,
      context_document: { documents: response.context_documents },
      response: response.response,
      created_at: response.created_at,
    };
    setMessages((prev) => [...prev, aiMessage]);
    
    // If this was the first message, trigger auto-rename callback
    if (isFirstMessage && onFirstMessage) {
      onFirstMessage(query);
    }
    
    return response;
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send message');
    // Remove the temporary user message on error
    setMessages((prev) => prev.filter(msg => msg.id !== userMessage.id));
    throw err;
  } finally {
    setSending(false);
  }
};
```

---

### Step 2: Implement Streaming Output

**Backend Changes Required:**

#### Option A: Server-Sent Events (SSE)
**File:** [`controllers/chat_messages.py`](controllers/chat_messages.py:51-79)

Modify the endpoint to use Server-Sent Events:

```python
from fastapi.responses import StreamingResponse
import json

@router.post("/query")
async def process_query_streaming(
    query_request: ChatQueryRequest,
    session: Session = Depends(get_db_session)
):
    """
    Process a chat query with streaming response.
    """
    async def generate_response():
        chat_message_service = ChatMessageService(session)
        
        # Get conversation context
        context = await chat_message_service.get_conversation_context(
            chat_id=query_request.chat_id,
            max_history=query_request.max_history
        )
        
        # Get retrieval context
        retrieval_context = await chat_message_service.get_retrieval_context(
            chat_id=query_request.chat_id,
            top_k=query_request.top_k,
            use_retrieval=query_request.use_retrieval
        )
        
        # Generate response with streaming
        async for chunk in chat_message_service.generate_streaming_response(
            query=query_request.query,
            context=context,
            retrieval_context=retrieval_context,
            llm_model=query_request.llm_model,
            llm_provider=query_request.llm_provider
        ):
            yield chunk
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )
```

#### Option B: WebSocket (Real-time)
**File:** Create new endpoint in [`controllers/chat_messages.py`](controllers/chat_messages.py)

```python
from fastapi import WebSocket

@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: str):
    """
    WebSocket endpoint for real-time chat streaming.
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            chat_message_service = ChatMessageService(session)
            
            # Process query and stream response
            async for chunk in chat_message_service.generate_streaming_response(
                query=data['query'],
                chat_id=chat_id
            ):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            await websocket.send_json({
                "type": "done",
                "message_id": "..."
            })
    except WebSocketDisconnect:
        pass
```

**Frontend Changes Required:**

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

Add streaming support:

```tsx
const sendMessage = async (userId: string, query: string, onFirstMessage?: (query: string) => void) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  
  // Add user message immediately
  const userMessage: ChatMessage = {
    id: `temp-${Date.now()}-user`,
    chat_id: chatId,
    chat_query: query,
    context_document: null,
    response: null,
    created_at: new Date().toISOString(),
  };
  setMessages((prev) => [...prev, userMessage]);
  
  try {
    const isFirstMessage = messages.length === 0;
    
    // Create AI message placeholder for streaming
    const aiMessageId = `temp-${Date.now()}-ai`;
    const aiMessage: ChatMessage = {
      id: aiMessageId,
      chat_id: chatId,
      chat_query: query,
      context_document: null,
      response: '', // Start with empty response
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, aiMessage]);
    
    // Fetch with streaming
    const response = await fetch(`${API_BASE_URL}/chat-messages/query/stream`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: chatId,
        query: query,
        use_retrieval: true,
        top_k: 5,
      }),
    });
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    
    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'chunk') {
              fullResponse += data.content;
              // Update AI message with new content
              setMessages((prev) => prev.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, response: fullResponse }
                  : msg
              ));
            } else if (data.type === 'done') {
              // Streaming complete
              // Update with final message ID and context
              setMessages((prev) => prev.map(msg => 
                msg.id === aiMessageId 
                  ? { 
                      ...msg, 
                      id: data.message_id,
                      context_document: { documents: data.context_documents }
                    }
                  : msg
              ));
              
              // Trigger auto-rename if first message
              if (isFirstMessage && onFirstMessage) {
                onFirstMessage(query);
              }
            }
          }
        }
      }
    }
    
    return { message_id: aiMessageId, response: fullResponse };
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send message');
    // Remove temporary messages on error
    setMessages((prev) => prev.filter(msg => 
      msg.id !== userMessage.id && msg.id !== aiMessageId
    ));
    throw err;
  } finally {
    setSending(false);
  }
};
```

---

## Implementation Approach Options

### Option 1: Simple Fix (Quick)
- **Only fix user message visibility**
- Keep non-streaming backend
- Add user message immediately before sending query
- **Effort:** Low
- **Time:** ~30 minutes

### Option 2: Full Streaming (Recommended)
- **Implement both user message visibility and streaming**
- Requires backend changes for SSE or WebSocket
- Provides best user experience
- **Effort:** High
- **Time:** ~2-3 hours

### Option 3: Hybrid Approach
- **Fix user message visibility now**
- Plan streaming implementation for later
- Allows incremental improvement
- **Effort:** Medium
- **Time:** ~1 hour for fix + planning for streaming

---

## Testing Checklist

### User Message Visibility
- [ ] User message appears immediately after sending
- [ ] User message shows "sending" indicator
- [ ] User message is removed if send fails
- [ ] AI response appears below user message

### Streaming Output
- [ ] AI response appears progressively as it's generated
- [ ] Typing indicator shows while generating
- [ ] Response completes gracefully
- [ ] Error handling for interrupted streams
- [ ] Context documents appear with final response

---

## Files to Modify

### For User Message Visibility Fix:
- [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

### For Full Streaming:
**Backend:**
- [`controllers/chat_messages.py`](controllers/chat_messages.py) - Add streaming endpoint
- [`services/chat_messages.py`](services/chat_messages.py) - Add streaming generation method
- [`services/chat.py`](services/chat.py) - Update to support streaming

**Frontend:**
- [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Add streaming logic
- [`frontend/lib/api.ts`](frontend/lib/api.ts) - Add streaming API function
- [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx) - Update to handle streaming messages

---

## Notes

- The user message visibility fix is straightforward and can be implemented quickly
- Streaming requires significant backend changes to support SSE or WebSocket
- Consider using existing streaming libraries like `aiosse` or `eventsource` for frontend
- Backend should use LangChain's streaming capabilities if available
- For LLM providers that support streaming (OpenAI, Anthropic), leverage their native streaming APIs
