# Chat Rename and Query Persistence Fixes Plan

## Issues Identified

### Issue 1: Need to be able to rename the chats

**Current State:**
- Backend already has a rename endpoint at `/chats/{chat_id}/rename` ([`controllers/chat.py:82-112`](controllers/chat.py:82-112))
- Frontend does not have any rename functionality

**Required Changes:**
1. Add `renameChat` function to API layer ([`frontend/lib/api.ts`](frontend/lib/api.ts))
2. Add `renameChat` function to useChats hook ([`frontend/hooks/useChats.ts`](frontend/hooks/useChats.ts))
3. Add UI elements to ChatSidebar ([`frontend/components/ChatSidebar.tsx`](frontend/components/ChatSidebar.tsx)) to allow renaming

**Implementation Approach:**
- Add a rename button (pencil icon) next to the delete button in the chat list
- When clicked, show an input field to edit the chat title
- Alternatively, allow double-click on the chat title to edit it

---

### Issue 2: User queries disappear after page refresh

**Root Cause:**
The backend stores a single message record with both `chat_query` and `response` populated ([`services/chat_messages.py:406-415`](services/chat_messages.py:406-415)):

```python
new_message = ChatMessage(
    chat_id=query_request.chat_id,
    chat_query=query_request.query,
    context_document={"documents": context_documents} if context_documents else None,
    response=result["response"],  # Always populated
    created_at=get_current_utc_time()
)
```

The frontend logic in [`ChatMessage.tsx:14`](frontend/components/ChatMessage.tsx:14) determines if a message is from the user:

```tsx
const isUser = !message.response;
```

Since `response` is always populated (not null), `isUser` becomes `false`, and only the AI response is displayed.

**Previous Fix Attempt:**
I modified [`useMessages.ts`](frontend/hooks/useMessages.ts:24-46) to add two separate messages when sending:
1. User message with `response: null`
2. AI message with full response data

However, only the AI message was saved to the database. When the page refreshes, messages are fetched from the database, and only the AI messages (with populated `response`) are returned.

**Solution:**
Modify the frontend to split each message from the backend into two separate messages when fetching:

1. **User Message:**
   - `id`: Generate a unique ID (e.g., `${originalId}-user`)
   - `chat_query`: Original query
   - `response`: `null` (this makes it display as a user message)
   - `context_document`: `null`
   - `created_at`: Original timestamp

2. **AI Message:**
   - `id`: Original ID
   - `chat_query`: Original query (for reference)
   - `response`: Original response
   - `context_document`: Original context documents
   - `created_at`: Original timestamp

This approach:
- Doesn't require backend changes
- Maintains the existing database schema
- Provides the expected chat UI pattern with separate user and AI messages
- Works consistently whether messages are newly sent or fetched from the database

---

## Implementation Plan

### Step 1: Add renameChat API function

**File:** [`frontend/lib/api.ts`](frontend/lib/api.ts)

**Add after `deleteChat` function:**

```tsx
export async function renameChat(chatId: string, newTitle: string): Promise<Chat> {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/rename`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(newTitle),
  });
  if (!response.ok) throw new Error('Failed to rename chat');
  return response.json();
}
```

---

### Step 2: Add renameChat to useChats hook

**File:** [`frontend/hooks/useChats.ts`](frontend/hooks/useChats.ts)

**Add import:**
```tsx
import { fetchChatsByUser, createChat, deleteChat, renameChat } from '@/lib/api';
```

**Add function:**
```tsx
const renameChat = async (chatId: string, newTitle: string) => {
  const updatedChat = await renameChat(chatId, newTitle);
  setChats((prev) => prev.map((c) => (c.id === chatId ? updatedChat : c)));
};
```

**Update return statement:**
```tsx
return { chats, loading, error, refresh, createNewChat, removeChat, renameChat };
```

---

### Step 3: Add rename UI to ChatSidebar

**File:** [`frontend/components/ChatSidebar.tsx`](frontend/components/ChatSidebar.tsx)

**Add import:**
```tsx
import { MessageSquare, Trash2, Plus, Pencil } from 'lucide-react';
```

**Add state for editing:**
```tsx
const [editingChatId, setEditingChatId] = useState<string | null>(null);
const [editingTitle, setEditingTitle] = useState('');
```

**Add to props:**
```tsx
interface ChatSidebarProps {
  selectedChatId: string | null;
  chats: Chat[];
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
}
```

**Add to component parameters:**
```tsx
export function ChatSidebar({
  selectedChatId,
  chats,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
}: ChatSidebarProps) {
```

**Add helper functions:**
```tsx
const handleStartEdit = (chatId: string, currentTitle: string) => {
  setEditingChatId(chatId);
  setEditingTitle(currentTitle || 'Untitled Chat');
};

const handleSaveEdit = (chatId: string) => {
  if (editingTitle.trim()) {
    onRenameChat(chatId, editingTitle.trim());
  }
  setEditingChatId(null);
  setEditingTitle('');
};

const handleCancelEdit = () => {
  setEditingChatId(null);
  setEditingTitle('');
};

const handleKeyDown = (e: React.KeyboardEvent, chatId: string) => {
  if (e.key === 'Enter') {
    handleSaveEdit(chatId);
  } else if (e.key === 'Escape') {
    handleCancelEdit();
  }
};
```

**Update chat item rendering:**
```tsx
{chats.map((chat) => (
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
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <MessageSquare className="w-4 h-4 flex-shrink-0" />
        {editingChatId === chat.id ? (
          <input
            type="text"
            value={editingTitle}
            onChange={(e) => setEditingTitle(e.target.value)}
            onBlur={() => handleSaveEdit(chat.id)}
            onKeyDown={(e) => handleKeyDown(e, chat.id)}
            className="bg-background text-foreground px-2 py-1 rounded text-sm w-full"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span
            className="font-medium truncate"
            onDoubleClick={() => handleStartEdit(chat.id, chat.title || 'Untitled Chat')}
          >
            {chat.title || 'Untitled Chat'}
          </span>
        )}
      </div>
      <div className="flex gap-1 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={(e) => {
            e.stopPropagation();
            handleStartEdit(chat.id, chat.title || 'Untitled Chat');
          }}
        >
          <Pencil className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={(e) => {
            e.stopPropagation();
            onDeleteChat(chat.id);
          }}
        >
          <Trash2 className="w-3 h-3" />
        </Button>
      </div>
    </div>
    <div className="text-xs text-muted-foreground">
      {formatDistanceToNow(new Date(chat.created_at), { addSuffix: true })}
    </div>
  </div>
))}
```

---

### Step 4: Fix user query persistence in useMessages

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

**Modify the `refresh` function to split messages:**

```tsx
const refresh = async () => {
  if (!chatId) return;
  setLoading(true);
  try {
    const data = await fetchMessagesByChat(chatId);
    
    // Split each message into user and AI messages
    const splitMessages: ChatMessage[] = [];
    data.forEach((msg) => {
      // Add user message
      splitMessages.push({
        id: `${msg.id}-user`,
        chat_id: msg.chat_id,
        chat_query: msg.chat_query,
        context_document: null,
        response: null, // This makes it display as a user message
        created_at: msg.created_at,
      });
      
      // Add AI message (if response exists)
      if (msg.response) {
        splitMessages.push({
          id: msg.id,
          chat_id: msg.chat_id,
          chat_query: msg.chat_query,
          context_document: msg.context_document,
          response: msg.response,
          created_at: msg.created_at,
        });
      }
    });
    
    setMessages(splitMessages);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to fetch messages');
  } finally {
    setLoading(false);
  }
};
```

**Update the `sendMessage` function to match the split pattern:**

```tsx
const sendMessage = async (userId: string, query: string) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
    // First, add the user message immediately
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}-user`, // Temporary ID
      chat_id: chatId,
      chat_query: query,
      context_document: null,
      response: null, // This makes it a user message
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Then send the query and get the AI response
    const response = await sendQuery(userId, chatId, query);
    
    // Add the AI response as a separate message
    const aiMessage: ChatMessage = {
      id: response.message_id,
      chat_id: response.chat_id,
      chat_query: query, // Keep the query for reference
      context_document: { documents: response.context_documents },
      response: response.response,
      created_at: response.created_at,
    };
    setMessages((prev) => [...prev, aiMessage]);
    
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

### Step 5: Update page.tsx to pass renameChat handler

**File:** [`frontend/app/page.tsx`](frontend/app/page.tsx)

**Update the useChats destructuring:**
```tsx
const { chats, createNewChat, removeChat, renameChat } = useChats(selectedUser?.id || null);
```

**Add rename handler:**
```tsx
const handleRenameChat = async (chatId: string, newTitle: string) => {
  await renameChat(chatId, newTitle);
};
```

**Update ChatSidebar props:**
```tsx
<ChatSidebar
  selectedChatId={selectedChatId}
  chats={chats}
  onSelectChat={handleSelectChat}
  onNewChat={handleNewChat}
  onDeleteChat={removeChat}
  onRenameChat={handleRenameChat}
/>
```

---

## Testing Checklist

### Rename Chat Feature
- [ ] Rename button appears next to delete button in chat list
- [ ] Clicking rename button shows input field with current title
- [ ] Double-clicking on chat title shows input field
- [ ] Pressing Enter saves the new title
- [ ] Pressing Escape cancels editing
- [ ] Clicking outside the input saves the new title
- [ ] Chat title updates in the sidebar after renaming
- [ ] Empty title is not saved (uses previous title or "Untitled Chat")

### User Query Persistence
- [ ] User queries are displayed when sending a message
- [ ] AI responses are displayed after receiving response
- [ ] User queries remain visible after page refresh
- [ ] AI responses remain visible after page refresh
- [ ] Both user and AI messages appear in correct order
- [ ] References (if any) appear with AI responses
- [ ] Conversation history is preserved across page refreshes

---

## Files to Modify

1. [`frontend/lib/api.ts`](frontend/lib/api.ts) - Add renameChat API function
2. [`frontend/hooks/useChats.ts`](frontend/hooks/useChats.ts) - Add renameChat function
3. [`frontend/components/ChatSidebar.tsx`](frontend/components/ChatSidebar.tsx) - Add rename UI
4. [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Split messages on fetch
5. [`frontend/app/page.tsx`](frontend/app/page.tsx) - Pass renameChat handler

---

## Notes

- The rename feature uses the existing backend endpoint, so no backend changes are needed
- The query persistence fix is a frontend-only solution that doesn't require backend changes
- The message splitting approach ensures consistency between newly sent messages and fetched messages
- Consider adding a `role` field to the backend schema in the future for better message type management
