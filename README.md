# Basic RAG

A personal learning project to build a **complete end-to-end RAG (Retrieval-Augmented Generation) system** from scratch — covering document ingestion, vector storage, conversational chat with document context, a React frontend, and an automated evaluation pipeline.

The system lets you upload PDF documents, embed them into a vector database, then ask questions about them in a chat interface. Answers are grounded in the text of your uploaded documents.

---

## What it does

1. **Upload PDFs** → text is extracted, cleaned, split into chunks, and embedded using a configurable model
2. **Store vectors** → chunks and their embeddings are saved in PostgreSQL with `pgvector`
3. **Chat** → questions trigger a retrieval step (cosine similarity search), the top matching chunks are injected as context into an LLM prompt, and the response is returned
4. **Evaluate** → a RAGAS-based pipeline measures Faithfulness, Answer Relevance, and Context Precision across your chat history

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.13) |
| Chat Workflow | LangGraph |
| Vector Storage | PostgreSQL + `pgvector` |
| Embeddings | `sentence-transformers` (local), OpenAI, HuggingFace |
| LLMs | OpenAI, Anthropic, Google Gemini, HuggingFace, Ollama, local HF |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Evaluation | RAGAS |
| Migrations | Alembic |

---

## Project Structure

```
Basic_RAG/
├── main.py                         # FastAPI app entry point
├── controllers/                    # HTTP routing
│   ├── companies.py
│   ├── users.py
│   ├── document_embedding.py
│   ├── chat.py
│   └── chat_messages.py
├── services/                       # Business logic
│   ├── document_embedding.py       # PDF extract → chunk → embed
│   ├── vectorizer.py               # Vectorizer implementations
│   ├── chat.py
│   └── chat_messages.py            # LangGraph RAG workflow
├── layers/                         # Data layer
│   ├── models.py                   # SQLModel ORM models
│   ├── schemas.py                  # Pydantic request/response schemas
│   └── dao/                        # DB query functions
├── alembic/versions/               # Migration scripts
├── evaluations/                    # RAGAS evaluation pipeline
│   ├── single_eval.py
│   ├── batch_runner.py
│   ├── run_evaluations.py          # CLI entry point
│   └── results/
└── frontend/                       # Next.js frontend
    ├── app/
    ├── components/
    ├── hooks/
    └── contexts/
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL with the `pgvector` extension enabled
- Node.js 18+ (for the frontend)

```sql
-- In your PostgreSQL database:
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend

```bash
# Install dependencies (using uv)
uv sync

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL and any LLM API keys

# Run migrations
alembic upgrade head

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev   # http://localhost:3000
```

### Environment Variables

```env
# Required
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Embedding (default: local sentence-transformers, no key needed)
VECTORIZER_TYPE=local
VECTORIZER_MODEL=all-MiniLM-L6-v2

# LLM API keys (add whichever providers you want to use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
HUGGINGFACEHUB_API_TOKEN=hf_...
```

---

## Workflow

### 1 — Create a Company

Companies hold the embedding model and LLM config for all their users and documents.

```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_type": "local",
    "llm_model": "gpt-4",
    "llm_provider": "openai"
  }'
```

### 2 — Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@acme.com", "name": "Alice", "company_id": "<company-uuid>"}'
```

### 3 — Upload a PDF

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@report.pdf" \
  -F "company_id=<company-uuid>" \
  -F "user_id=<user-uuid>" \
  -F "chunk_size=1000" \
  -F "overlap=200"
```

The server extracts text, splits it into overlapping chunks, generates embeddings, and stores them as `DocumentVector` rows.

### 4 — Start a Chat

```bash
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user-uuid>",
    "company_id": "<company-uuid>",
    "title": "Q4 Analysis",
    "selected_document_ids": ["<doc-uuid>"]
  }'
```

> `selected_document_ids` is optional — omit it to search across all of the user's documents.

### 5 — Ask a Question

```bash
curl -X POST "http://localhost:8000/api/v1/chat-messages/query" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "<chat-uuid>",
    "query": "What was the total revenue in Q4?",
    "use_retrieval": true,
    "top_k": 5
  }'
```

The LangGraph workflow: embed the query → cosine similarity search → inject top-k chunks as context → LLM generates an answer → save and return the `ChatMessage`.

---

## API Overview

| Resource | Endpoint prefix |
|---|---|
| Companies | `/api/v1/companies/` |
| Users | `/api/v1/users/` |
| Documents | `/api/v1/documents/` |
| Chats | `/api/v1/chats/` |
| Chat Messages | `/api/v1/chat-messages/` |

Full interactive docs at **http://localhost:8000/docs**.

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload & embed a PDF |
| `POST` | `/api/v1/documents/upload/batch` | Upload up to 10 PDFs |
| `POST` | `/api/v1/documents/search` | Semantic search (`query`, `limit`) |
| `POST` | `/api/v1/chats/` | Create chat session |
| `GET` | `/api/v1/chats/user/{user_id}` | List user's chats |
| `POST` | `/api/v1/chat-messages/query` | Send query (full RAG pipeline) |
| `GET` | `/api/v1/chat-messages/chat/{chat_id}` | Get chat history |
| `PUT` | `/api/v1/companies/{id}/llm-config` | Update company LLM settings |

---

## Frontend

A Next.js chat interface for driving the entire backend without writing any API calls manually.

**Usage:**
1. Select a company and user from the dropdowns
2. Create a new chat (optionally select which documents to search)
3. Type a question — the response appears with source references
4. Use the file upload button to add more PDFs

**Main components:**

| Component | Role |
|---|---|
| `CompanyUserSelector` | Company/user picker (no auth) |
| `ChatSidebar` | Chat list with create/rename/delete |
| `ChatInterface` + `ChatMessage` | Message thread with markdown rendering |
| `FileUpload` | Drag-and-drop PDF upload |
| `DocumentSelector` | Scope a chat to specific files |
| `ReferenceCard` | Displays source chunks used in a response |

---

## Supported Models

### Embedding

| `embedding_type` | Notes |
|---|---|
| `local` | `sentence-transformers` — runs offline, no key needed |
| `openai` | `text-embedding-ada-002` — requires `OPENAI_API_KEY` |
| `huggingface` | HuggingFace Inference API — requires `HUGGINGFACE_API_KEY` |

### LLM

| `llm_provider` | Notes |
|---|---|
| `openai` | GPT-4 etc. — requires `OPENAI_API_KEY` |
| `anthropic` | Claude family — requires `ANTHROPIC_API_KEY` |
| `google` | Gemini — requires `GOOGLE_API_KEY` |
| `huggingface` | HuggingFace Hub — requires `HUGGINGFACEHUB_API_TOKEN` |
| `ollama` | Local Ollama server (default `http://localhost:11434`) |
| `local_hf` | Local HuggingFace pipeline; CUDA optional |

---

## RAGAS Evaluation

Measure RAG quality over your chat history using three metrics:

- **Faithfulness** — is the answer supported by the retrieved context?
- **Answer Relevance** — does the answer address the question?
- **Context Precision** — are the retrieved chunks actually relevant?

```bash
# Evaluate last 7 days for a company
python -m evaluations.run_evaluations --company-id <uuid>

# All time
python -m evaluations.run_evaluations --company-id <uuid> --days 0

# Single query
python -m evaluations.run_evaluations --single \
  --question "What is the revenue?" \
  --answer "Revenue was $42M in Q4." \
  --contexts "Q4 revenue reached $42M."
```

Results are saved to `evaluations/results/` as JSON and optionally to the database. See [evaluations/README.md](evaluations/README.md) for the full reference.

---

## Troubleshooting

**pgvector not found**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Ollama connection refused**
```bash
curl http://localhost:11434/api/tags   # check it's running
ollama pull llama2                     # download a model
```

**PDF returns no text** — the PDF may be image-only (scanned). Use `preview_only=true` to check before uploading.

**Evaluation requires `OPENAI_API_KEY`** — set it in your shell or `.env` before running the evaluation CLI.

For local model setup details, see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).
