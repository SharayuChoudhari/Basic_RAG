# Chat UI Fixes: Scrollbar and Title Truncation

## Issues Identified

### Issue 1: Scrollbar Not Working in Chat Sidebar
**Problem**: Users cannot scroll up or down in the chat session section of the UI. The scrollbar is not functioning properly.

**Root Cause**: The `ChatSidebar` component lacks proper height constraints. The `ScrollArea` component uses `flex-1` but the parent container doesn't have a defined height, preventing the scroll area from calculating its dimensions correctly.

**Current Structure**:
```
page.tsx (h-screen flex flex-col)
  └─ div (flex-1 flex overflow-hidden)
      └─ div (w-80 flex-shrink-0 border-r flex flex-col) [Sidebar Container]
          ├─ CompanyUserSelector
          ├─ div (p-4) with FileUpload
          └─ ChatSidebar (w-full border-r bg-muted/10 flex flex-col) [Missing flex-1]
              ├─ div (p-4 border-b) [New Chat Button]
              └─ ScrollArea (flex-1) [Chat List]
```

**Solution**: Add `flex-1` class to the `ChatSidebar` root div so it fills the remaining vertical space in the sidebar container, allowing the `ScrollArea` to properly calculate its height.

### Issue 2: Chat Title Truncation
**Problem**: Chat session titles that exceed 20 characters should display "..." at the end.

**Current Implementation**: The title uses CSS `truncate` class which visually truncates with ellipsis, but doesn't actually limit the character count to 20.

**Solution**: Create a helper function to truncate titles to 20 characters and append "..." if the title is longer.

## Implementation Plan

### Fix 1: Scrollbar Issue in ChatSidebar

**File**: `frontend/components/ChatSidebar.tsx`

**Change**: Update line 73 to add `flex-1` class to the root div.

**Before**:
```tsx
<div className="w-full border-r bg-muted/10 flex flex-col">
```

**After**:
```tsx
<div className="w-full border-r bg-muted/10 flex flex-col flex-1">
```

**Explanation**: Adding `flex-1` ensures the ChatSidebar component takes up all remaining vertical space in the parent container, which allows the ScrollArea (with `flex-1`) to properly calculate its height and enable scrolling.

### Fix 2: Chat Title Truncation

**File**: `frontend/components/ChatSidebar.tsx`

**Changes**:

1. Add a helper function at the top of the component (after imports, before the component definition):

```tsx
const truncateTitle = (title: string, maxLength: number = 20): string => {
  if (!title) return 'Untitled Chat';
  return title.length > maxLength ? title.slice(0, maxLength) + '...' : title;
};
```

2. Update line 48 (handleStartEdit function) to use the truncated title:

**Before**:
```tsx
setEditingTitle(currentTitle || 'Untitled Chat');
```

**After**:
```tsx
setEditingTitle(currentTitle || 'Untitled Chat');
```

3. Update line 116 (title display) to use the truncated title:

**Before**:
```tsx
{chat.title || 'Untitled Chat'}
```

**After**:
```tsx
{truncateTitle(chat.title || 'Untitled Chat')}
```

4. Update line 127 (edit button handler) to use the full title:

**Before**:
```tsx
handleStartEdit(chat.id, chat.title || 'Untitled Chat');
```

**After**:
```tsx
handleStartEdit(chat.id, chat.title || 'Untitled Chat');
```

**Note**: The edit functionality should still use the full title, not the truncated version, so users can edit the complete title.

## Testing Checklist

After implementing these fixes:

1. **Scrollbar Testing**:
   - [ ] Create multiple chat sessions (more than can fit in the visible area)
   - [ ] Verify that the scrollbar appears
   - [ ] Test scrolling up and down using the scrollbar
   - [ ] Test scrolling using mouse wheel
   - [ ] Test scrolling using keyboard (Page Up/Down, Arrow keys)
   - [ ] Verify that the last chat is always accessible when scrolling

2. **Title Truncation Testing**:
   - [ ] Create a chat with a title shorter than 20 characters - verify it displays fully
   - [ ] Create a chat with a title exactly 20 characters - verify it displays fully without "..."
   - [ ] Create a chat with a title longer than 20 characters - verify it shows first 20 chars + "..."
   - [ ] Double-click to edit a truncated title - verify the full title appears in the edit input
   - [ ] Edit a truncated title and save - verify the truncation still works correctly
   - [ ] Verify the "Untitled Chat" default title displays correctly

## Files to Modify

1. `frontend/components/ChatSidebar.tsx` - Both fixes will be applied to this file

## Summary

These are straightforward fixes that will significantly improve the user experience:

1. **Scrollbar fix**: A single class addition (`flex-1`) to enable proper scrolling in the chat sidebar
2. **Title truncation**: A helper function to limit titles to 20 characters with "..." suffix, while preserving the full title for editing

Both fixes are minimal, focused, and won't affect other parts of the application.
