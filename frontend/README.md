# RAG Chatbot Frontend

A React + Next.js frontend for the RAG chatbot with shadcn/ui components.

## Features

- **Company/User Selection**: Dropdown selectors to choose company and user (no login required)
- **Chat Interface**: Real-time chat with bot responses
- **Chat History**: User-wise chat history maintained
- **File Upload**: Upload PDF documents for embedding
- **Reference Display**: Show context documents used for bot responses
- **Future-Ready**: Designed for easy migration to authentication system

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Date Formatting**: date-fns

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Main chat page
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── CompanyUserSelector.tsx
│   ├── ChatSidebar.tsx
│   ├── ChatInterface.tsx
│   ├── ChatMessage.tsx
│   ├── ReferenceCard.tsx
│   ├── FileUpload.tsx
│   └── ChatInput.tsx
├── lib/
│   ├── api.ts              # API client functions
│   └── utils.ts            # Utility functions
├── hooks/
│   ├── useCompanies.ts
│   ├── useUsers.ts
│   ├── useChats.ts
│   └── useMessages.ts
├── types/
│   └── api.ts              # TypeScript types
├── contexts/
│   ├── AuthContext.tsx      # Auth state (for future login)
│   └── AppContext.tsx       # App state (company, user)
└── .env.local              # Environment variables
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Backend API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/companies` | GET | Get all companies |
| `/api/v1/users` | GET | Get all users |
| `/api/v1/users/company/{company_id}` | GET | Get users by company |
| `/api/v1/chats/user/{user_id}` | GET | Get chats for user |
| `/api/v1/chats/user/{user_id}` | POST | Create chat for user |
| `/api/v1/chats/{chat_id}` | DELETE | Delete chat |
| `/api/v1/chat-messages/chat/{chat_id}` | GET | Get messages for chat |
| `/api/v1/chat-messages/query/user/{user_id}/chat/{chat_id}` | POST | Send query |
| `/api/v1/documents/upload` | POST | Upload PDF document |

## Future Login Migration

The frontend is designed for easy migration to an authentication system:

1. **AuthContext**: Already includes `setDemoUser` function for current demo mode
2. **API Client**: `getAuthHeaders()` function ready to add auth tokens
3. **Component Structure**: All components use context-based state management
4. **Migration Path**:
   - Replace `setDemoUser` calls with actual `login` function
   - Add JWT token storage in localStorage
   - Add route guards for protected pages
   - Replace CompanyUserSelector with login form

## Usage

1. Select a company from the dropdown
2. Select a user from the dropdown (filtered by company)
3. Create a new chat or select an existing one
4. Chat with the bot
5. Upload PDF documents for embedding
6. View references for bot responses
