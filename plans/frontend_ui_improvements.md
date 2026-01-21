# Frontend UI Improvements Plan

## Overview
This plan outlines the changes needed to improve the frontend UI based on three requirements:
1. Move PDF upload button under the choose company and user dropdowns
2. Enable scrolling to see previous messages when sending a query
3. Show references with only document name and chunk index

---

## Current State Analysis

### Component Structure
```
page.tsx
├── CompanyUserSelector (dropdowns for company and user)
├── ChatSidebar (chat list)
└── ChatInterface
    ├── ScrollArea
    │   ├── Messages list
    │   └── FileUpload (currently inside scroll area)
    └── ChatInput (outside scroll area)
```

### Reference Data Structure
Each reference contains:
- `document_id`: UUID of the document
- `chunk_index`: Index of the chunk (0, 1, 2, ...)
- `content`: Text content of the chunk
- `metadata`: Object containing `filename` and other metadata
- `similarity`: Similarity score

---

## Implementation Plan

### Requirement 1: Move PDF Upload Button

**Files to modify:**
- [`frontend/app/page.tsx`](frontend/app/page.tsx)
- [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx)

**Changes:**
1. Remove `<FileUpload />` from [`ChatInterface.tsx`](frontend/components/ChatInterface.tsx:71)
2. Add `<FileUpload />` component in [`page.tsx`](frontend/app/page.tsx) below the `CompanyUserSelector` component
3. Wrap `CompanyUserSelector` and `FileUpload` in a container div for proper layout

**Expected layout:**
```
┌─────────────────────────────────────┐
│  Header (RAG Chatbot)               │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐ │
│  │ CompanyUserSelector           │ │
│  │ [Company ▼] [User ▼]         │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ FileUpload                    │ │
│  │ [Select PDF Files]            │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  ChatSidebar  │  ChatInterface       │
│               │  ┌─────────────────┐│
│               │  │ Messages (scroll)││
│               │  └─────────────────┘│
│               │  ┌─────────────────┐│
│               │  │ ChatInput        ││
│               │  └─────────────────┘│
└─────────────────────────────────────┘
```

---

### Requirement 2: Enable Scrolling for Previous Messages

**Files to modify:**
- [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx)

**Changes:**
1. After moving `FileUpload` out of the scroll area (from Requirement 1), the scroll area will only contain messages
2. The existing `useEffect` that auto-scrolls to bottom on new messages should remain
3. The `ChatInput` is already outside the scroll area, so users can scroll up while typing

**Current behavior:**
- `ScrollArea` wraps both messages and `FileUpload`
- This takes up vertical space and limits scrolling

**Expected behavior:**
- `ScrollArea` only wraps messages
- Users can scroll through all previous messages
- Input remains visible at the bottom

---

### Requirement 3: Simplify Reference Display

**Files to modify:**
- [`frontend/components/ReferenceCard.tsx`](frontend/components/ReferenceCard.tsx)

**Changes:**
1. Remove the similarity score badge
2. Remove the content preview (currently shows 3 lines of content)
3. Display only:
   - Document name (from `reference.metadata.filename`)
   - Chunk index (from `reference.chunk_index`)

**Current display:**
```
┌─────────────────────────────────────┐
│ 📄 Document.pdf              85%    │
│ This is a preview of the content... │
│ that shows up to 3 lines of text... │
└─────────────────────────────────────┘
```

**Expected display:**
```
┌─────────────────────────────────────┐
│ 📄 Document.pdf - Chunk 3          │
└─────────────────────────────────────┘
```

**Implementation details:**
- Format: `{filename} - Chunk {chunk_index + 1}` (using 1-based indexing for user-friendliness)
- Keep the card styling but simplify the content
- Remove the `similarity_score` badge
- Remove the content preview paragraph

---

## Summary of Changes

| File | Changes |
|------|---------|
| [`frontend/app/page.tsx`](frontend/app/page.tsx) | Add `FileUpload` component below `CompanyUserSelector` |
| [`frontend/components/ChatInterface.tsx`](frontend/components/ChatInterface.tsx) | Remove `FileUpload` component from scroll area |
| [`frontend/components/ReferenceCard.tsx`](frontend/components/ReferenceCard.tsx) | Simplify to show only filename and chunk index |

---

## Testing Checklist

After implementation, verify:
- [ ] PDF upload button appears below company/user dropdowns
- [ ] Upload functionality still works correctly
- [ ] Messages can be scrolled to view previous conversations
- [ ] Chat input remains visible while scrolling
- [ ] References show only document name and chunk number
- [ ] No content preview or similarity score in references
- [ ] Layout is responsive on different screen sizes
