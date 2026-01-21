# Alternative Approach: Display Query and Response in Single Message

## Overview

Instead of splitting messages into two separate data points, we can modify the [`ChatMessage`](frontend/components/ChatMessage.tsx:13-58) component to display both the user query and the AI response in a single message bubble.

## Benefits

- No need to split messages into two data points
- No backend changes required
- Simpler data structure
- Both query and response are always visible together
- Maintains the original message ID

## Implementation

### Modify ChatMessage Component

**File:** [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx)

**Current Logic:**
```tsx
const isUser = !message.response;
// ...
{isUser ? message.chat_query : message.response}
```

**New Logic:**
Always display both the query and response in a single message bubble:

```tsx
export function ChatMessage({ message }: ChatMessageProps) {
  const references = message.context_document?.documents || [];
  const hasResponse = !!message.response;

  return (
    <div className="flex gap-3 justify-start">
      <Avatar className="w-8 h-8 flex-shrink-0">
        <AvatarFallback>
          <Bot className="w-5 h-5" />
        </AvatarFallback>
      </Avatar>
      <div className="max-w-[80%]">
        <Card className="p-4 bg-muted">
          {/* User Query Section */}
          <div className="mb-3 pb-3 border-b border-border">
            <div className="text-xs font-medium text-muted-foreground mb-1">You:</div>
            <div className="whitespace-pre-wrap break-words">
              {message.chat_query}
            </div>
          </div>
          
          {/* AI Response Section */}
          {hasResponse && (
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">Assistant:</div>
              <div className="whitespace-pre-wrap break-words">
                {message.response}
              </div>
            </div>
          )}
        </Card>
        
        {/* References */}
        {!hasResponse && references.length > 0 && (
          <div className="mt-2 space-y-2">
            <div className="text-xs font-medium text-muted-foreground">References:</div>
            {references.map((ref: any, idx: number) => (
              <ReferenceCard key={idx} reference={ref} />
            ))}
          </div>
        )}
        
        {/* Timestamp */}
        <div className="text-xs text-muted-foreground mt-1">
          {new Date(message.created_at).toLocaleString()}
        </div>
      </div>
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
    
    // Add the message with both query and response
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

**The `refresh` function can remain as-is** (no splitting needed):

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

The message will look like this:

```
┌─────────────────────────────────────┐
│ 🤖                                │
│ ┌─────────────────────────────────┐   │
│ │ You:                          │   │
│ │ What is the capital of France?   │   │
│ ├─────────────────────────────────┤   │
│ │ Assistant:                     │   │
│ │ The capital of France is Paris.  │   │
│ │ It's known for the Eiffel Tower │   │
│ │ and the Louvre Museum.          │   │
│ └─────────────────────────────────┘   │
│ References:                        │
│ [Document 1] [Document 2]         │
│ Jan 21, 2026, 3:45 PM          │
└─────────────────────────────────────┘
```

## Comparison with Split Approach

| Aspect | Split Approach | Single Message Approach |
|---------|----------------|----------------------|
| Data Structure | Two messages per exchange | One message per exchange |
| Backend Changes | None | None |
| Frontend Complexity | Higher (splitting logic) | Lower (simpler logic) |
| Chat UI Pattern | Standard (separate bubbles) | Non-standard (combined bubble) |
| Message ID | Two IDs (one temp, one real) | One ID (original) |
| Query Visibility | Always visible | Always visible |
| Response Visibility | Always visible | Always visible |
| References | With AI message | With message |

## Pros and Cons

### Single Message Approach (Recommended)

**Pros:**
- Simpler implementation
- No message splitting logic
- Maintains original message IDs
- Both query and response always visible together
- No backend changes needed

**Cons:**
- Doesn't match typical chat UI pattern
- All messages appear on the left side (AI style)
- Less visual distinction between user and AI

### Split Approach

**Pros:**
- Matches typical chat UI pattern
- User messages on right, AI on left
- Clear visual distinction

**Cons:**
- More complex implementation
- Requires message splitting logic
- Temporary IDs for user messages
- More data points to manage

## Recommendation

The **single message approach** is recommended because:
1. It's simpler to implement and maintain
2. It doesn't require splitting messages
3. Both query and response are always visible together
4. It maintains the original message structure
5. No backend changes needed

If you prefer the standard chat UI pattern with separate user/AI bubbles, then the split approach would be better, but it requires more complex logic.

## Files to Modify

1. [`frontend/components/ChatMessage.tsx`](frontend/components/ChatMessage.tsx) - Modify to display both query and response
2. [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Revert to single-message approach

## Testing Checklist

- [ ] User query is displayed in the message
- [ ] AI response is displayed in the message
- [ ] Both query and response are visible after page refresh
- [ ] References (if any) appear with the message
- [ ] Timestamp is displayed correctly
- [ ] Message styling looks good
- [ ] No console errors
