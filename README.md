<div align="center">

# 🔍 Basic RAG

**A full-stack Retrieval-Augmented Generation system**

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL+pgvector-14+-336791?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![LangGraph](https://img.shields.io/badge/LangGraph-powered-FF6B35?style=flat)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

Upload PDFs → Embed & Store → Chat with your documents

[Features](#-features) · [Quick Start](#-quick-start) · [Workflow](#-workflow) · [API Reference](#-api-reference) · [Frontend](#-frontend) · [Evaluation](#-ragas-evaluation-pipeline)

</div>

---

## ✨ Features

| | Feature | Details |
|---|---|---|
| 📄 | **Document Ingestion** | Upload single or batch PDFs; auto-extract, clean, chunk, and embed |
| 🧠 | **Multiple Embedding Models** | Local (`sentence-transformers`), OpenAI, HuggingFace Inference API |
| 🏢 | **Multi-Tenant** | Per-company embedding model and LLM configuration |
| 🗄️ | **Vector Storage** | PostgreSQL + `pgvector` with variable-length vectors and JSONB metadata |
| 🔍 | **Semantic Search** | Cosine-similarity search over stored document chunks |
| 💬 | **Conversational Chat** | LangGraph workflow: retrieval → generation with conversation history |
| 🤖 | **Multiple LLM Providers** | OpenAI, Anthropic, Google Gemini, HuggingFace, Ollama, local HF pipeline |
| 📌 | **Document Scoping** | Pin a chat to specific documents for focused retrieval |
| 📊 | **RAG Evaluation** | RAGAS metrics: Faithfulness, Answer Relevance, Context Precision |
| 🖥️ | **React Frontend** | Next.js 15 + Tailwind CSS + shadcn/ui chat interface |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Frontend  (Next.js 15)                       │
│   CompanySelector ─ ChatSidebar ─ ChatInterface ─ FileUpload     │
└───────────────────────────┬──────────────────────────────────────┘
                            │  REST / JSON
┌───────────────────────────▼──────────────────────────────────────┐
│                     Backend  (FastAPI)                           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  📥 Document Upload Pipeline                            │  │
│   │  PDF ──► text extract ──► clean & chunk ──► vectorize   │  │
│   │       ──► store DocumentVector rows (pgvector)          │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  💬 Chat Query Pipeline  (LangGraph)                    │  │
│   │  query ──► embed ──► cosine search ──► top-k chunks     │  │
│   │        ──► LLM generation ──► persist ChatMessage       │  │
│   └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│         PostgreSQL + pgvector  (Database)                        │
│  companies · users · document_vectors · chats · chat_messages    │
│  evaluation_jobs · evaluation_results                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Basic_RAG/
├── main.py                         # FastAPI app, router registration
├── pyproject.toml                  # Dependencies
├── .env.example                    # Environment variable template
├── alembic.ini                     # Migration config
│
├── controllers/                    # HTTP layer
│   ├── companies.py
│   ├── users.py
│   ├── document_embedding.py
│   ├── chat.py
│   └── chat_messages.py
│
├── services/                       # Business logic
│   ├── document_embedding.py       # PDF extract → chunk → embed
│   ├── vectorizer.py               # Local / OpenAI / HuggingFace
│   ├── chat.py                     # Chat CRUD
│   └── chat_messages.py            # LangGraph RAG workflow
│
├── layers/                         # Data layer
│   ├── database.py                 # SQLModel engine & session
│   ├── models.py                   # ORM models
│   ├── schemas.py                  # Pydantic schemas
│   └── dao/                        # Data access objects
│
├── alembic/versions/               # Migration scripts
│
├── evaluations/                    # RAGAS evaluation pipeline
│   ├── single_eval.py
│   ├── batch_runner.py
│   ├── dataset_loader.py
│   ├── metrics_store.py
│   ├── run_evaluations.py          # CLI entry point
│   └── results/                    # JSON output files
│
├── frontend/                       # Next.js frontend
│   ├── app/                        # App Router pages
│   ├── components/                 # React components
│   ├── hooks/                      # Custom React hooks
│   └── contexts/                   # React context providers
│
└── docs/                           # Additional documentation
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 14+ with the `pgvector` extension
- Node.js 18+ (for the frontend)
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

```sql
-- Enable pgvector in your database
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend

```bash
# 1. Clone and enter the project
git clone <repository-url> && cd Basic_RAG

# 2. Install Python dependencies
uv sync          # recommended
# pip install -e .  # or with pip

# 3. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and API keys

# 4. Run migrations
alembic upgrade head

# 5. Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **API Docs**: http://localhost:8000/docs  
> **ReDoc**: http://localhost:8000/redoc

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev     # http://localhost:3000
```

---

## ⚙️ Configuration

### `/.env` (backend)

```env
# ── Database ──────────────────────────────────────────
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# ── Default Embedding (overridden per-company) ────────
VECTORIZER_TYPE=local              # local | openai | huggingface
VECTORIZER_MODEL=all-MiniLM-L6-v2

# ── LLM API Keys ──────────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
HUGGINGFACEHUB_API_TOKEN=hf_...

# ── RAGAS Evaluation ──────────────────────────────────
EVAL_LLM_MODEL=gpt-4
EVAL_LLM_PROVIDER=openai
EVAL_BATCH_SIZE=10
EVAL_OUTPUT_DIR=evaluations/results
EVAL_SAVE_TO_DB=true
EVAL_SAVE_TO_JSON=true
```

For local LLM setup (Ollama, local HuggingFace models), see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).

---

## 🔄 Workflow

Follow these five steps to go from a fresh database to a working RAG chat.

### Step 1 — Create a Company

A company holds the embedding model and LLM settings used by all its users and documents.

```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_type": "local",
    "llm_model": "gpt-4",
    "llm_provider": "openai",
    "llm_temperature": 0.7
  }'
```

<details>
<summary>Response</summary>

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corp",
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_type": "local",
  "llm_model": "gpt-4",
  "llm_provider": "openai",
  "llm_temperature": 0.7,
  "llm_max_tokens": null,
  "created_at": "2024-01-12T10:00:00"
}
```
</details>

---

### Step 2 — Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@acme.com",
    "name": "Alice",
    "company_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

### Step 3 — Upload Documents

The service: extracts text from the PDF → cleans it → splits into overlapping chunks → embeds each chunk using the company's vectorizer → stores `DocumentVector` rows in PostgreSQL.

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@report.pdf" \
  -F "company_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "user_id=660e8400-e29b-41d4-a716-446655440001" \
  -F "chunk_size=1000" \
  -F "overlap=200" \
  -F "clean_text=true"
```

<details>
<summary>Response</summary>

```json
{
  "status": "success",
  "document_id": "770e8400-e29b-41d4-a716-446655440002",
  "filename": "report.pdf",
  "text_length": 18500,
  "num_chunks": 19,
  "chunk_size": 1000,
  "overlap": 200,
  "metadata": {
    "filename": "report.pdf",
    "file_size": 204800,
    "pdf_metadata": { "title": "Annual Report", "page_count": 24 }
  }
}
```
</details>

---

### Step 4 — Create a Chat Session

Optionally scope the chat to specific documents — retrieval will only search those files.

```bash
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Q4 Analysis",
    "selected_document_ids": ["770e8400-e29b-41d4-a716-446655440002"]
  }'
```

> If `selected_document_ids` is omitted, retrieval searches **all** documents owned by the user.

---

### Step 5 — Send a Query

The LangGraph workflow:
1. Embeds the query using the company's embedding model
2. Performs cosine-similarity search over matching `DocumentVector` rows
3. Injects the top-k chunks as context into the LLM prompt
4. Generates a grounded answer
5. Persists the `ChatMessage` (query + context + response)

```bash
curl -X POST "http://localhost:8000/api/v1/chat-messages/query" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "880e8400-e29b-41d4-a716-446655440003",
    "query": "What was the total revenue in Q4?",
    "use_retrieval": true,
    "top_k": 5,
    "max_history": 10
  }'
```

<details>
<summary>Response</summary>

```json
{
  "message_id": "990e8400-e29b-41d4-a716-446655440004",
  "chat_id": "880e8400-...",
  "query": "What was the total revenue in Q4?",
  "response": "Based on Document 1, the total revenue in Q4 was $42.3 million, representing a 12% YoY increase...",
  "context_documents": [
    {
      "document_id": "770e8400-...",
      "chunk_index": 7,
      "content": "Q4 revenue reached $42.3M...",
      "similarity": 0.94
    }
  ],
  "created_at": "2024-01-12T10:04:00",
  "llm_model": "gpt-4",
  "llm_provider": "openai"
}
```
</details>

---

## 📡 API Reference

### Companies

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/companies/` | Create company |
| `GET` | `/api/v1/companies/` | List all companies |
| `GET` | `/api/v1/companies/{id}` | Get company by ID |
| `PUT` | `/api/v1/companies/{id}` | Update company |
| `PUT` | `/api/v1/companies/{id}/embedding-model` | Update embedding model only |
| `PUT` | `/api/v1/companies/{id}/llm-config` | Update LLM config (query params) |
| `DELETE` | `/api/v1/companies/{id}` | Delete company |

<details>
<summary>LLM config examples</summary>

```bash
# Ollama (local)
curl -X PUT "http://localhost:8000/api/v1/companies/{id}/llm-config?llm_model=llama2&llm_provider=ollama&llm_endpoint=http://localhost:11434"

# OpenAI
curl -X PUT "http://localhost:8000/api/v1/companies/{id}/llm-config?llm_model=gpt-4&llm_provider=openai"

# Anthropic
curl -X PUT "http://localhost:8000/api/v1/companies/{id}/llm-config?llm_model=claude-3-sonnet-20240229&llm_provider=anthropic"
```

Supported providers: `openai` · `anthropic` · `google` · `huggingface` · `ollama` · `local_hf`
</details>

---

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/users/` | Create user |
| `GET` | `/api/v1/users/` | List all users |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `GET` | `/api/v1/users/email/{email}` | Get user by email |
| `PUT` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Delete user |
| `GET` | `/api/v1/users/{id}/company` | Get user's company details |

---

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload & embed a single PDF |
| `POST` | `/api/v1/documents/upload/batch` | Upload & embed up to 10 PDFs |
| `GET` | `/api/v1/documents/{document_id}` | Retrieve chunks for a document |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete document and all chunks |
| `POST` | `/api/v1/documents/search` | Semantic search (form: `query`, `limit`) |

<details>
<summary>Upload parameters</summary>

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | **required** | PDF file |
| `company_id` | UUID | optional | Use company's embedding model |
| `user_id` | UUID | optional | Document owner |
| `chunk_size` | int | 1000 | Characters per chunk |
| `overlap` | int | 200 | Overlap between chunks |
| `preview_only` | bool | false | Extract text only, skip embedding |
| `clean_text` | bool | true | Normalise whitespace/encoding |
| `skip_empty_chunks` | bool | true | Skip blank chunks |
| `metadata` | JSON string | optional | Extra JSONB metadata |
</details>

---

### Chats

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chats/` | Create chat session |
| `GET` | `/api/v1/chats/user/{user_id}` | List user's chats |
| `PUT` | `/api/v1/chats/{chat_id}/rename` | Rename a chat |
| `DELETE` | `/api/v1/chats/{chat_id}` | Delete chat + all messages |
| `GET` | `/api/v1/chats/documents/company/{company_id}` | List documents for a company |

---

### Chat Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat-messages/query` | Process query (full RAG pipeline) |
| `GET` | `/api/v1/chat-messages/chat/{chat_id}` | Fetch all messages in a chat |
| `DELETE` | `/api/v1/chat-messages/{message_id}` | Delete a message |

<details>
<summary>Query request body</summary>

```json
{
  "chat_id": "<uuid>",
  "query": "Your question here",
  "use_retrieval": true,
  "top_k": 5,
  "max_history": 10,
  "llm_model": null,
  "llm_provider": null
}
```

> `llm_model` and `llm_provider` override company settings when provided.
</details>

---

### Health Check

```
GET /health  →  {"status": "healthy"}
GET /        →  {"message": "RAG Document Embedding API", "version": "0.1.0", ...}
```

---

## 🗄️ Database Schema

<details>
<summary>companies</summary>

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | auto |
| `name` | String | indexed |
| `description` | String | optional |
| `embedding_model` | String | indexed |
| `embedding_type` | String | `local` · `openai` · `huggingface` |
| `llm_model` | String | indexed |
| `llm_provider` | String | indexed |
| `llm_endpoint` | String | for local models |
| `llm_api_key` | String | stored key |
| `llm_temperature` | Float | default 0.7 |
| `llm_max_tokens` | Integer | optional |
| `created_at` | Timestamp | |
</details>

<details>
<summary>users</summary>

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | auto |
| `email` | String | unique, indexed |
| `name` | String | |
| `company_id` | UUID FK | → companies |
| `created_at` | Timestamp | |
</details>

<details>
<summary>document_vectors</summary>

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | auto |
| `content` | Text | chunk text |
| `embedding` | Vector | variable-length pgvector column |
| `meta_data` | JSONB | filename, page count, custom fields |
| `document_id` | UUID | indexed; groups chunks |
| `chunk_index` | Integer | order within document |
| `user_id` | UUID | indexed |
| `company_id` | UUID | indexed; optional |
| `created_at` | Timestamp | |
</details>

<details>
<summary>chats</summary>

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `title` | String | optional |
| `user_id` | UUID FK | → users, indexed |
| `company_id` | UUID FK | → companies, indexed |
| `selected_document_ids` | JSONB | scoped retrieval |
| `created_at` | Timestamp | |
| `updated_at` | Timestamp | |
</details>

<details>
<summary>chat_messages</summary>

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `chat_id` | UUID FK | → chats, indexed |
| `chat_query` | String | indexed |
| `context_document` | JSONB | retrieved chunks |
| `response` | String | LLM answer |
| `status` | String | `processing` · `done` · `error` |
| `created_at` | Timestamp | |
</details>

---

## 🖥️ Frontend

A **Next.js 15** (App Router) + **TypeScript** + **Tailwind CSS** + **shadcn/ui** chat interface.

### Key Components

| Component | Description |
|-----------|-------------|
| `CompanyUserSelector` | Select company & user (no login required) |
| `ChatSidebar` | List, create, rename, and delete chats |
| `ChatInterface` | Scrollable message thread |
| `ChatInput` | Text input with send handler |
| `ChatMessage` | Renders markdown responses |
| `FileUpload` | Drag-and-drop PDF upload with progress |
| `DocumentSelector` | Scope a chat to specific uploaded documents |
| `ReferenceCard` | Shows source chunks used in a response |

### Usage

1. Select a **company**, then a **user**
2. Click **New Chat** in the sidebar
3. (Optional) Select specific documents to restrict retrieval
4. Type a question and press **Send**
5. Responses appear with source references inline
6. Use **File Upload** to add more PDFs at any time

---

## 📊 RAGAS Evaluation Pipeline

Automatically measure the quality of your RAG system using RAGAS.

### Metrics

| Metric | What it measures |
|--------|-----------------|
| **Faithfulness** | Is the answer supported by the retrieved context? |
| **Answer Relevance** | Does the answer address the question? |
| **Context Precision** | Are the retrieved chunks relevant to the question? |

### CLI Usage

```bash
# Evaluate last 7 days (default)
python -m evaluations.run_evaluations --company-id <uuid>

# Evaluate last 30 days
python -m evaluations.run_evaluations --company-id <uuid> --days 30

# Evaluate all time
python -m evaluations.run_evaluations --company-id <uuid> --days 0

# Preview scope without running
python -m evaluations.run_evaluations --preview --company-id <uuid>

# Dry run — no DB writes
python -m evaluations.run_evaluations --company-id <uuid> --dry-run

# Single query evaluation
python -m evaluations.run_evaluations --single \
  --question "What is the revenue?" \
  --answer "Revenue was $42M in Q4." \
  --contexts "Q4 revenue reached $42M." "Financial summary shows growth."
```

Results are saved as JSON to `evaluations/results/` and optionally to the `evaluation_jobs` / `evaluation_results` tables. See [evaluations/README.md](evaluations/README.md) for the full reference.

---

## 🛠️ Development

### Supported Embedding Types

| `embedding_type` | Library | API Key |
|-----------------|---------|---------|
| `local` | `sentence-transformers` | None |
| `openai` | `openai` Python client | `OPENAI_API_KEY` |
| `huggingface` | HuggingFace Inference API | `HUGGINGFACE_API_KEY` |

### Supported LLM Providers

| `llm_provider` | Service | Credential |
|----------------|---------|-----------|
| `openai` | OpenAI API | `OPENAI_API_KEY` |
| `anthropic` | Anthropic API | `ANTHROPIC_API_KEY` |
| `google` | Google Gemini | `GOOGLE_API_KEY` |
| `huggingface` | HuggingFace Hub | `HUGGINGFACEHUB_API_TOKEN` |
| `ollama` | Ollama (local) | `llm_endpoint` (default `http://localhost:11434`) |
| `local_hf` | Local HuggingFace pipeline | Model downloaded locally; CUDA optional |

### Database Migrations

```bash
# After editing models.py
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🔧 Troubleshooting

<details>
<summary>pgvector extension not found</summary>

```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```
</details>

<details>
<summary>API key errors</summary>

```bash
# Check keys are exported
echo $OPENAI_API_KEY

# Or verify they are in your .env file
grep OPENAI_API_KEY .env
```
</details>

<details>
<summary>Ollama connection refused</summary>

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# List downloaded models
ollama list

# Pull a model if needed
ollama pull llama2
```
</details>

<details>
<summary>PDF returns empty text</summary>

- The PDF may be image-only (scanned). Text extraction requires a text-layer PDF.
- Test with `preview_only=true` before committing embeddings.
- Password-protected PDFs are not supported.
</details>

<details>
<summary>Local HuggingFace model out-of-memory</summary>

- Use a smaller model (e.g. `gpt2`).  
- Enable CUDA: `python -c "import torch; print(torch.cuda.is_available())"`.
- Reduce `llm_max_tokens` for the company's config.
</details>

<details>
<summary>Evaluation: OPENAI_API_KEY is required</summary>

```bash
export OPENAI_API_KEY=sk-...
python -m evaluations.run_evaluations --company-id <uuid>
```
</details>

For detailed local model documentation, see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).

---

## 📄 License

[MIT](LICENSE) — feel free to use, modify, and distribute.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.
