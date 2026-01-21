# Chat Message Display Without Data Splitting

## Overview

Modify the [`ChatMessage`](frontend/components/ChatMessage.tsx:13-58) component to display both user query and AI response in a single message object, but style them to look like separate bubbles. This maintains the current UI appearance without creating unnecessary data points.

## Key Points

- **No data splitting**: Keep single message object with both `chat_query` and `response`
- **No backend changes**: Use existing data structure
- **Current UI appearance**: Maintain separate user and AI bubble look
- **Query persistence**: Both query and response visible after refresh

## Implementation

### Modify ChatMessage Component

**File:** [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx)

**Replace the entire component with:**

```tsx
'use client';

import { ChatMessage as ChatMessageType } from '@/types/api';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User } from 'lucide-react';
import { ReferenceCard } from './ReferenceCard';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const references = message.context_document?.documents || [];
  const hasResponse = !!message.response;

  return (
    <div className="space-y-4">
      {/* User Query Bubble */}
      <div className="flex gap-3 justify-end">
        <div className="max-w-[80%]">
          <Card className="p-4 bg-primary text-primary-foreground">
            <div className="whitespace-pre-wrap break-words">
              {message.chat_query}
            </div>
          </Card>
          <div className="text-xs text-muted-foreground mt-1 text-right">
            {new Date(message.created_at).toLocaleString()}
          </div>
        </div>
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarFallback>
            <User className="w-5 h-5" />
          </AvatarFallback>
        </Avatar>
      </div>

      {/* AI Response Bubble */}
      {hasResponse && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-8 h-8 flex-shrink-0">
            <AvatarFallback>
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[80%]">
            <Card className="p-4 bg-muted">
              <div className="whitespace-pre-wrap break-words">
                {message.response}
              </div>
            </Card>
            {references.length > 0 && (
              <div className="mt-2 space-y-2">
                <div className="text-xs font-medium text-muted-foreground">References:</div>
                {references.map((ref: any, idx: number) => (
                  <ReferenceCard key={idx} reference={ref} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

### Revert useMessages Changes

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

**Revert the `sendMessage` function to the original single-message approach:**

```tsx
const sendMessage = async (userId: string, query: string) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
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
    
    return response;
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send message');
    throw err;
  } finally {
    setSending(false);
  }
};
```

**The `refresh` function remains as-is (no changes needed):**

```tsx
const refresh = async () => {
  if (!chatId) return;
  setLoading(true);
  try {
    const data = await fetchMessagesByChat(chatId);
    setMessages(data); // No splitting needed
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to fetch messages');
  } finally {
    setLoading(false);
  }
};
```

## Visual Design

Each message object will render as two separate bubbles:

```
┌─────────────────────────────────────────┐
│                          [User Avatar] │
│                    ┌───────────────┐  │
│                    │ User Query    │  │
│                    │ What is...?   │  │
│                    └───────────────┘  │
│                    Jan 21, 3:45 PM     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [Bot Avatar]                          │
│ ┌───────────────┐                    │
│ │ AI Response   │                    │
│ │ The capital   │                    │
│ │ is Paris...   │                    │
│ └───────────────┘                    │
│ References:                            │
│ [Document 1] [Document 2]             │
└─────────────────────────────────────────┘
```

## Key Changes

### Before (Current Implementation)
- Used `const isUser = !message.response;` to determine message type
- Displayed either user query OR AI response (not both)
- User queries disappeared after refresh

### After (New Implementation)
- Always display both user query and AI response
- User query appears on the right (blue bubble)
- AI response appears on the left (gray bubble)
- Both visible after refresh
- No data splitting required

## Benefits

1. **No Data Splitting**: Single message object contains both query and response
2. **No Backend Changes**: Uses existing data structure
3. **Current UI Appearance**: Maintains separate user and AI bubble look
4. **Query Persistence**: Both query and response visible after refresh
5. **Simpler Logic**: No complex splitting/merging logic
6. **Original IDs**: Maintains original message IDs

## Files to Modify

1. [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx) - Modify to display both query and response
2. [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Revert to single-message approach

## Testing Checklist

- [ ] User query is displayed in blue bubble on the right
- [ ] AI response is displayed in gray bubble on the left
- [ ] Both query and response are visible after page refresh
- [ ] References (if any) appear with AI response
- [ ] Timestamp is displayed correctly
- [ ] Message styling matches current UI
- [ ] No console errors
- [ ] Scroll functionality works correctly
- [ ] Multiple messages display correctly in sequence

## Notes

- This approach maintains the visual appearance of separate user and AI bubbles
- No actual data splitting occurs - it's purely a UI rendering change
- The backend data structure remains unchanged
- Each message object renders as two visual bubbles (user + AI)
- This is the simplest solution that meets all requirements
