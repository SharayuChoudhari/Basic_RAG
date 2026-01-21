# API Endpoints with user_id Parameter

## Overview
This document describes the new API endpoints that accept `user_id` as a path parameter for creating chats and chat messages.

## New Endpoints

### 1. Create Chat for User
**Endpoint**: `POST /chats/user/{user_id}`

**Description**: Creates a new chat session for a specific user.

**Path Parameters**:
- `user_id` (UUID, required): ID of the user to create chat for

**Query Parameters**:
- `title` (string, optional): Title for the chat
- `company_id` (UUID, optional): Company ID to associate with the chat

**Response**: [`ChatResponse`](layers/schemas.py:194)

**Example Request**:
```bash
POST /chats/user/123e4567-e89b-12d3-a456-426614174000?title=My%20Chat
```

**Example Response**:
```json
{
  "id": "456e7890-e12f-34d5-b678-537925285111",
  "title": "My Chat",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "company_id": null,
  "created_at": "2026-01-18T12:00:00.000Z",
  "updated_at": "2026-01-18T12:00:00.000Z"
}
```

**Implementation**: [`controllers/chat.py:45`](controllers/chat.py:45)

---

### 2. Create Chat Message for User
**Endpoint**: `POST /chat-messages/user/{user_id}/chat/{chat_id}`

**Description**: Creates a new chat message for a specific user and chat.

**Path Parameters**:
- `user_id` (UUID, required): ID of the user
- `chat_id` (UUID, required): ID of the chat

**Query Parameters**:
- `chat_query` (string, required): The user's query/message
- `context_document` (dict, optional): Context document with retrieved documents
- `response` (string, optional): AI response

**Response**: [`ChatMessageResponse`](layers/schemas.py:227)

**Example Request**:
```bash
POST /chat-messages/user/123e4567-e89b-12d3-a456-426614174000/chat/456e7890-e12f-34d5-b678-537925285111?chat_query=What%20is%20the%20weather%20today?
```

**Example Response**:
```json
{
  "id": "789e0123-f34a-56b7-c890-648036396222",
  "chat_id": "456e7890-e12f-34d5-b678-537925285111",
  "chat_query": "What is the weather today?",
  "context_document": null,
  "response": null,
  "created_at": "2026-01-18T12:00:00.000Z"
}
```

**Implementation**: [`controllers/chat_messages.py:79`](controllers/chat_messages.py:79)

---

### 3. Process Query for User
**Endpoint**: `POST /chat-messages/query/user/{user_id}/chat/{chat_id}`

**Description**: Processes a chat query for a specific user and chat using LangGraph workflow with retrieval and LLM generation, including conversation context.

**Path Parameters**:
- `user_id` (UUID, required): ID of the user
- `chat_id` (UUID, required): ID of the chat

**Query Parameters**:
- `query` (string, required): The user's query
- `use_retrieval` (boolean, optional, default: true): Whether to use document retrieval
- `top_k` (integer, optional, default: 5): Number of top documents to retrieve
- `llm_model` (string, optional): LLM model name
- `llm_provider` (string, optional): LLM provider
- `max_history` (integer, optional, default: 10): Maximum number of previous messages to include in context

**Response**: [`ChatQueryResponse`](layers/schemas.py:254)

**Example Request**:
```bash
POST /chat-messages/query/user/123e4567-e89b-12d3-a456-426614174000/chat/456e7890-e12f-34d5-b678-537925285111?query=What%20was%20the%20second%20point%20you%20mentioned?&max_history=5
```

**Example Response**:
```json
{
  "message_id": "789e0123-f34a-56b7-c890-648036396222",
  "chat_id": "456e7890-e12f-34d5-b678-537925285111",
  "query": "What was the second point you mentioned?",
  "response": "The second point I mentioned was about the importance of context awareness in chat systems...",
  "context_documents": [],
  "created_at": "2026-01-18T12:00:00.000Z",
  "llm_model": "gpt-4",
  "llm_provider": "openai"
}
```

**Implementation**: [`controllers/chat_messages.py:47`](controllers/chat_messages.py:47)

---

## Comparison with Existing Endpoints

### Chat Endpoints

| Endpoint | Method | Input | Description |
|-----------|--------|--------|-------------|
| `/chats/` | POST | Request body with `user_id` | Create chat (existing) |
| `/chats/user/{user_id}` | POST | Path parameter `user_id` | Create chat for user (new) |

### Chat Message Endpoints

| Endpoint | Method | Input | Description |
|-----------|--------|--------|-------------|
| `/chat-messages/` | POST | Request body with `chat_id` | Create message (existing) |
| `/chat-messages/user/{user_id}/chat/{chat_id}` | POST | Path parameters `user_id`, `chat_id` | Create message for user (new) |
| `/chat-messages/query` | POST | Request body with `chat_id` | Process query (existing) |
| `/chat-messages/query/user/{user_id}/chat/{chat_id}` | POST | Path parameters `user_id`, `chat_id` | Process query for user (new) |

## Benefits

1. **Simplified API**: Clients can use path parameters instead of constructing request bodies
2. **User-Centric**: Endpoints are organized around user actions
3. **RESTful Design**: Follows REST principles with resource-based URLs
4. **Backward Compatible**: Existing endpoints remain unchanged
5. **Flexible**: Both approaches (body and path parameters) are available

## Usage Examples

### Using cURL

#### Create Chat for User
```bash
curl -X POST "http://localhost:8000/chats/user/123e4567-e89b-12d3-a456-426614174000?title=My%20New%20Chat" \
  -H "Content-Type: application/json"
```

#### Create Chat Message for User
```bash
curl -X POST "http://localhost:8000/chat-messages/user/123e4567-e89b-12d3-a456-426614174000/chat/456e7890-e12f-34d5-b678-537925285111?chat_query=Hello%20world" \
  -H "Content-Type: application/json"
```

#### Process Query for User with Conversation Context
```bash
curl -X POST "http://localhost:8000/chat-messages/query/user/123e4567-e89b-12d3-a456-426614174000/chat/456e7890-e12f-34d5-b678-537925285111?query=What%20did%20you%20say%20earlier?&max_history=10&use_retrieval=true" \
  -H "Content-Type: application/json"
```

### Using Python requests

```python
import requests

# Create chat for user
response = requests.post(
    "http://localhost:8000/chats/user/123e4567-e89b-12d3-a456-426614174000",
    params={"title": "My New Chat"}
)
chat = response.json()

# Create chat message for user
response = requests.post(
    f"http://localhost:8000/chat-messages/user/123e4567-e89b-12d3-a456-426614174000/chat/{chat['id']}",
    params={"chat_query": "Hello world"}
)
message = response.json()

# Process query for user with conversation context
response = requests.post(
    f"http://localhost:8000/chat-messages/query/user/123e4567-e89b-12d3-a456-426614174000/chat/{chat['id']}",
    params={
        "query": "What did you say earlier?",
        "max_history": 10,
        "use_retrieval": True
    }
)
query_response = response.json()
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Files Modified

1. [`controllers/chat.py`](controllers/chat.py) - Added `POST /chats/user/{user_id}` endpoint
2. [`controllers/chat_messages.py`](controllers/chat_messages.py) - Added `POST /chat-messages/user/{user_id}/chat/{chat_id}` and `POST /chat-messages/query/user/{user_id}/chat/{chat_id}` endpoints

## Future Enhancements

Potential improvements for future iterations:

1. **Batch Operations**: Support for creating multiple chats/messages in a single request
2. **User Validation**: Add authentication/authorization to verify user access
3. **Rate Limiting**: Implement rate limiting per user
4. **Pagination**: Add pagination for chat and message lists
5. **Filtering**: Add filtering options for chat and message queries

## Conclusion

The new API endpoints provide a user-centric approach to creating chats and chat messages, with `user_id` as a path parameter. This offers a more intuitive and RESTful API design while maintaining backward compatibility with existing endpoints.
