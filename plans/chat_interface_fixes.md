# Chat Interface Fixes Plan

## Issues Identified

### Issue 1: Not able to scroll in the chat part of the app

**Root Cause:**
In [`ChatInterface.tsx`](frontend/components/ChatInterface.tsx:45-47), there's a nested structure with conflicting scroll containers:

```tsx
<ScrollArea ref={scrollAreaRef} className="flex-1">
  <div className="flex-1 flex flex-col">
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Messages */}
    </div>
  </div>
</ScrollArea>
```

**Problems:**
1. The `ScrollArea` component from Radix UI provides its own viewport with scrolling capabilities
2. The inner div has `overflow-y-auto` which conflicts with the ScrollArea's viewport
3. Multiple nested `flex-1` containers create height calculation issues
4. The ScrollArea's viewport needs proper height constraints to work correctly

**Fix:**
- Remove `overflow-y-auto` from the inner div
- Simplify the nested structure to avoid multiple `flex-1` containers
- Ensure the ScrollArea's viewport has proper height constraints
- The ScrollArea should be the only container handling scrolling

---

### Issue 2: Not seeing the user query in the chat part of the app

**Root Cause:**
In [`ChatMessage.tsx`](frontend/components/ChatMessage.tsx:14-35), the logic for determining if a message is from the user is:

```tsx
const isUser = !message.response;
// ...
{isUser ? message.chat_query : message.response}
```

**Problems:**
1. When a new message is sent via [`useMessages.ts`](frontend/hooks/useMessages.ts:30-37), it creates a `ChatMessage` object with both `chat_query` and `response` populated
2. Since `response` is populated (not null/undefined), `isUser` becomes `false`
3. This causes the component to display the AI response instead of the user query
4. The user's query is never displayed in the chat interface

**Current Message Creation Flow:**
```tsx
// In useMessages.ts, when sending a message:
const newMessage: ChatMessage = {
  id: response.message_id,
  chat_id: response.chat_id,
  chat_query: response.query,  // User's query
  context_document: { documents: response.context_documents },
  response: response.response,  // AI's response
  created_at: response.created_at,
};
setMessages((prev) => [...prev, newMessage]);
```

**Fix Options:**

**Option A: Split into two separate messages (Recommended)**
- Create two separate message entries: one for the user query and one for the AI response
- This matches the typical chat UI pattern where user and AI messages are separate
- Requires backend changes to store messages differently

**Option B: Add a `role` field to distinguish message types**
- Add a `role` field to the `ChatMessage` type (e.g., 'user' | 'assistant')
- Use this field to determine message styling and content
- Requires backend schema changes

**Option C: Display both query and response in a single message**
- Modify the `ChatMessage` component to display both the query and response
- Less ideal as it doesn't match typical chat UI patterns

**Recommended Fix (Option A - Frontend-only workaround):**
Since we want to minimize backend changes, we can create a frontend-only solution:
1. When sending a message, add two separate entries to the messages array:
   - First entry: User message with `response: null`
   - Second entry: AI message with `chat_query: ''` (or the original query)
2. This way, both messages will be displayed correctly

---

## Implementation Plan

### Step 1: Fix Scroll Issue in ChatInterface

**File:** [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx)

**Changes:**
1. Remove `overflow-y-auto` from the inner messages container
2. Simplify the nested structure
3. Ensure proper height constraints

**Before:**
```tsx
<ScrollArea ref={scrollAreaRef} className="flex-1">
  <div className="flex-1 flex flex-col">
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Messages */}
    </div>
  </div>
</ScrollArea>
```

**After:**
```tsx
<ScrollArea ref={scrollAreaRef} className="flex-1">
  <div className="p-4 space-y-4">
    {/* Messages */}
  </div>
</ScrollArea>
```

---

### Step 2: Fix User Query Display Issue

**File:** [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts)

**Changes:**
1. Modify the `sendMessage` function to add two separate messages
2. First message: User query with `response: null`
3. Second message: AI response with the full response data

**Before:**
```tsx
const sendMessage = async (userId: string, query: string) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
    const response = await sendQuery(userId, chatId, query);
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

**After:**
```tsx
const sendMessage = async (userId: string, query: string) => {
  if (!chatId) throw new Error('No chat selected');
  setSending(true);
  try {
    // First, add the user message immediately
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(), // Temporary ID
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

## Additional Issue Found: Missing ScrollBar Component

**Root Cause:**
The [`ScrollArea`](frontend/components/ui/scroll-area.tsx:6-19) component is incomplete. According to Radix UI documentation, the ScrollArea requires both the `Viewport` and `ScrollBar` components to work properly. The current implementation only includes the `Viewport`, which means the scrollbar won't appear and scrolling won't function correctly.

**Fix:**
Add the `ScrollBar` component to the ScrollArea implementation.

**Before:**
```tsx
const ScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root
    ref={ref}
    className={cn("relative overflow-hidden", className)}
    {...props}
  >
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">
      {children}
    </ScrollAreaPrimitive.Viewport>
  </ScrollAreaPrimitive.Root>
))
```

**After:**
```tsx
const ScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root
    ref={ref}
    className={cn("relative overflow-hidden", className)}
    {...props}
  >
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">
      {children}
    </ScrollAreaPrimitive.Viewport>
    <ScrollBar />
    <ScrollAreaPrimitive.Corner />
  </ScrollAreaPrimitive.Root>
))

const ScrollBar = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>
>(({ className, orientation = "vertical", ...props }, ref) => (
  <ScrollAreaPrimitive.ScrollAreaScrollbar
    ref={ref}
    orientation={orientation}
    className={cn(
      "flex touch-none select-none transition-colors",
      orientation === "vertical" &&
        "h-full w-2.5 border-l border-l-transparent p-[1px]",
      orientation === "horizontal" &&
        "h-2.5 flex-col border-t border-t-transparent p-[1px]",
      className
    )}
    {...props}
  >
    <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-border" />
  </ScrollAreaPrimitive.ScrollAreaScrollbar>
))
ScrollBar.displayName = ScrollAreaPrimitive.ScrollAreaScrollbar.displayName
```

## Testing Checklist

After implementing the fixes:

### Scroll Issue
- [ ] Chat messages area scrolls properly when there are many messages
- [ ] Scrollbar appears and functions correctly
- [ ] Auto-scroll to bottom works when new messages are added
- [ ] Manual scrolling works without issues

### User Query Display
- [ ] User's query is displayed in the chat interface
- [ ] User message appears on the right side (styled as user message)
- [ ] AI response appears on the left side (styled as AI message)
- [ ] Both query and response are visible in the conversation
- [ ] References (if any) appear with the AI response

### General
- [ ] No console errors
- [ ] Layout remains responsive
- [ ] Chat input remains accessible at the bottom
- [ ] Loading indicator works correctly

---

## Files to Modify

1. [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx) - Fix scroll issue
2. [`frontend/hooks/useMessages.ts`](frontend/hooks/useMessages.ts) - Fix user query display

---

## Notes

- The scroll fix is straightforward and should resolve the scrolling issue immediately
- The user query display fix uses a frontend-only approach to avoid backend changes
- The two-message approach (user + AI) is the standard pattern for chat interfaces
- Consider adding a `role` field to the backend schema in the future for better message type management
