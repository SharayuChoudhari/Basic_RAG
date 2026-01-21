# Basic RAG - Document Embedding API

A FastAPI-based service for uploading PDF documents, creating embeddings, and storing them in a PostgreSQL database with pgvector support for semantic search.

## Features

- **PDF Upload**: Upload PDF files and automatically extract text
- **Batch Upload**: Upload multiple PDF files in a single request
- **File Validation**: Comprehensive validation for file size, type, and content
- **PDF Metadata Extraction**: Automatically extract title, author, page count, and more
- **Preview Mode**: Preview extracted text before creating embeddings
- **Text Cleaning**: Optional text normalization and cleaning
- **Document Chunking**: Intelligent text chunking with configurable size and overlap
- **Multiple Vectorizers**: Support for local, OpenAI, and HuggingFace embeddings
- **Vector Storage**: Store embeddings in PostgreSQL using pgvector
- **Semantic Search**: Search for similar documents using vector similarity
- **RESTful API**: Clean and well-documented FastAPI endpoints
- **Local LLM Support**: Use local models like Ollama or HuggingFace for chat responses
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Google, HuggingFace, Ollama, and local models
- **Company-Specific LLM Config**: Each company can configure their preferred LLM provider

## Project Structure

```
Basic_RAG/
├── main.py                          # FastAPI application entry point
├── controllers/
│   └── document_embedding.py        # API endpoints for document operations
├── services/
│   ├── document_embedding.py        # Document embedding service
│   └── vectorizer.py                # Vectorizer implementations
├── layers/
│   ├── database.py                  # Database configuration
│   ├── models.py                    # SQLModel database models
│   └── dao/
│       └── document_vectors_dao.py  # Data access object for document vectors
├── alembic/                         # Database migrations
├── .env.example                     # Environment variables template
└── pyproject.toml                   # Project dependencies
```

## Prerequisites

- Python 3.13 or higher
- PostgreSQL with pgvector extension
- (Optional) OpenAI API key for OpenAI embeddings
- (Optional) HuggingFace API key for HuggingFace embeddings
- (Optional) Ollama for local LLM support
- (Optional) CUDA-capable GPU for local HuggingFace models

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Basic_RAG
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # or using uv
   uv sync
   ```

3. **Set up PostgreSQL with pgvector**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Vectorizer Configuration
# Options: local, openai, huggingface
VECTORIZER_TYPE=local

# Local Vectorizer Configuration
VECTORIZER_MODEL=all-MiniLM-L6-v2

# OpenAI Configuration (required if VECTORIZER_TYPE=openai)
OPENAI_API_KEY=your_openai_api_key_here

# HuggingFace Configuration (required if VECTORIZER_TYPE=huggingface)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# LLM Provider Configuration (for chat functionality)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

For detailed information on configuring local models (Ollama, local HuggingFace), see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).

## Running the Application

Start the FastAPI server:

```bash
python main.py
# or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Companies API

#### 1. Create Company

**Endpoint**: `POST /api/v1/companies/`

Create a new company with embedding model settings.

**Request Body**:
```json
{
  "name": "Acme Corp",
  "description": "Technology company",
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_type": "local"
}
```

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "description": "Technology company",
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_type": "local"
  }'
```

**Response**:
```json
{
  "id": 1,
  "name": "Acme Corp",
  "description": "Technology company",
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_type": "local",
  "created_at": "2024-01-12T10:00:00"
}
```

#### 2. Get All Companies

**Endpoint**: `GET /api/v1/companies/`

Retrieve all companies.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/companies/"
```

#### 3. Get Company by ID

**Endpoint**: `GET /api/v1/companies/{company_id}`

Get a specific company by ID.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/companies/1"
```

#### 4. Update Company

**Endpoint**: `PUT /api/v1/companies/{company_id}`

Update company details.

**Request Body**:
```json
{
  "name": "Updated Company Name",
  "description": "Updated description",
  "embedding_model": "text-embedding-ada-002",
  "embedding_type": "openai"
}
```

**Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding_model": "text-embedding-ada-002",
    "embedding_type": "openai"
  }'
```

#### 5. Update Company Embedding Model

**Endpoint**: `PUT /api/v1/companies/{company_id}/embedding-model`

Update only the embedding model settings for a company.

**Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1/embedding-model?embedding_model=text-embedding-ada-002&embedding_type=openai"
```

#### 6. Update Company LLM Configuration

**Endpoint**: `PUT /api/v1/companies/{company_id}/llm-config`

Update the LLM configuration for a company (supports local models like Ollama).

**Query Parameters**:
- `llm_model` (required): Model name (e.g., "llama2", "mistral", "gpt-4")
- `llm_provider` (required): Provider type (`openai`, `anthropic`, `google`, `huggingface`, `ollama`, `local_hf`)
- `llm_endpoint` (optional): Endpoint URL for local models (e.g., "http://localhost:11434")
- `llm_api_key` (optional): API key for cloud providers
- `llm_temperature` (optional, default: 0.7): Temperature for generation
- `llm_max_tokens` (optional): Max tokens for generation

**Example using Ollama**:
```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1/llm-config?llm_model=llama2&llm_provider=ollama&llm_endpoint=http://localhost:11434&llm_temperature=0.7"
```

**Example using local HuggingFace**:
```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1/llm-config?llm_model=gpt2&llm_provider=local_hf&llm_temperature=0.8&llm_max_tokens=500"
```

**Example using OpenAI**:
```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1/llm-config?llm_model=gpt-4&llm_provider=openai&llm_temperature=0.7"
```

For more details on local model setup, see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).

#### 7. Delete Company

**Endpoint**: `DELETE /api/v1/companies/{company_id}`

Delete a company.

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/companies/1"
```

### Users API

#### 1. Create User

**Endpoint**: `POST /api/v1/users/`

Create a new user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "company_id": 1
}
```

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "company_id": 1
  }'
```

**Response**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "company_id": 1,
  "created_at": "2024-01-12T10:00:00"
}
```

#### 2. Get All Users

**Endpoint**: `GET /api/v1/users/`

Retrieve all users.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/"
```

#### 3. Get User by ID

**Endpoint**: `GET /api/v1/users/{user_id}`

Get a specific user by ID.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/1"
```

#### 4. Get User by Email

**Endpoint**: `GET /api/v1/users/email/{email}`

Get a user by email address.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/email/user@example.com"
```

#### 5. Update User

**Endpoint**: `PUT /api/v1/users/{user_id}`

Update user details.

**Request Body**:
```json
{
  "name": "Updated Name",
  "company_id": 2
}
```

**Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name"
  }'
```

#### 6. Delete User

**Endpoint**: `DELETE /api/v1/users/{user_id}`

Delete a user.

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/users/1"
```

#### 7. Get User's Company

**Endpoint**: `GET /api/v1/users/{user_id}/company`

Get the company associated with a user.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/1/company"
```

**Response**:
```json
{
  "company_id": 1,
  "name": "Acme Corp",
  "description": "Technology company",
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_type": "local",
  "llm_model": "llama2",
  "llm_provider": "ollama",
  "llm_endpoint": "http://localhost:11434",
  "llm_temperature": 0.7,
  "llm_max_tokens": 1000
}
```

### Documents API

### 1. Upload PDF Document (Enhanced)

**Endpoint**: `POST /api/v1/documents/upload`

Upload a PDF file, extract text, create embeddings, and store in the database with enhanced features.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): PDF file
  - `company_id` (optional): Company ID to use company-specific embedding model settings
  - `user_id` (optional): User ID for the document
  - `chunk_size` (optional, default: 1000): Size of each chunk in characters
  - `overlap` (optional, default: 200): Overlap between chunks in characters
  - `metadata` (optional): Additional metadata as JSON string
  - `preview_only` (optional, default: false): If true, only preview extracted text without creating embeddings
  - `skip_empty_chunks` (optional, default: true): Skip chunks with no text content
  - `clean_text` (optional, default: true): Clean and normalize text before processing

**Example using curl**:
```bash
# Upload and process with company-specific embedding model
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -F "file=@document.pdf" \
  -F "company_id=1" \
  -F "user_id=1" \
  -F "chunk_size=1000" \
  -F "overlap=200" \
  -F "clean_text=true"

# Preview only (no processing)
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -F "file=@document.pdf" \
  -F "preview_only=true"
```

**Example using Python**:
```python
import requests

url = "http://localhost:8000/api/v1/documents/upload"
files = {"file": open("document.pdf", "rb")}
data = {
    "company_id": 1,  # Uses company's embedding model settings
    "user_id": 1,
    "chunk_size": 1000,
    "overlap": 200,
    "clean_text": True,
    "skip_empty_chunks": True
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response (Success)**:
```json
{
  "status": "success",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "text_length": 15000,
  "num_chunks": 15,
  "chunk_size": 1000,
  "overlap": 200,
  "metadata": {
    "filename": "document.pdf",
    "file_size": 102400,
    "pdf_metadata": {
      "title": "Document Title",
      "author": "Author Name",
      "page_count": 10
    }
  },
  "processing_info": {
    "pages_processed": 10,
    "text_cleaned": true,
    "empty_chunks_skipped": true
  }
}
```

**Response (Preview)**:
```json
{
  "status": "preview",
  "filename": "document.pdf",
  "text_length": 15000,
  "text_preview": "First 1000 characters of extracted text...",
  "estimated_chunks": 15,
  "metadata": {
    "filename": "document.pdf",
    "pdf_metadata": {
      "page_count": 10
    }
  }
}
```

### 2. Batch Upload PDF Documents

**Endpoint**: `POST /api/v1/documents/upload/batch`

Upload multiple PDF files in a single request.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `files` (required): Multiple PDF files (max 10)
  - `company_id` (optional): Company ID to use company-specific embedding model settings
  - `user_id` (optional): User ID for the documents
  - `chunk_size` (optional, default: 1000): Size of each chunk in characters
  - `overlap` (optional, default: 200): Overlap between chunks in characters
  - `metadata` (optional): Additional metadata as JSON string (applied to all files)
  - `skip_empty_chunks` (optional, default: true): Skip chunks with no text content
  - `clean_text` (optional, default: true): Clean and normalize text before processing

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload/batch" \
  -H "accept: application/json" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf" \
  -F "company_id=1" \
  -F "user_id=1" \
  -F "chunk_size=1000"
```

**Example using Python**:
```python
import requests

url = "http://localhost:8000/api/v1/documents/upload/batch"
files = [
    ("files", open("document1.pdf", "rb")),
    ("files", open("document2.pdf", "rb")),
    ("files", open("document3.pdf", "rb"))
]
data = {
    "company_id": 1,  # Uses company's embedding model settings
    "user_id": 1,
    "chunk_size": 1000,
    "clean_text": True
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response**:
```json
{
  "status": "completed",
  "total_files": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "status": "success",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document1.pdf",
      "text_length": 15000,
      "num_chunks": 15,
      "metadata": {...}
    },
    {
      "status": "success",
      "document_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "document2.pdf",
      "text_length": 20000,
      "num_chunks": 20,
      "metadata": {...}
    }
  ],
  "errors": [
    {
      "filename": "document3.pdf",
      "error": "No text could be extracted from the PDF"
    }
  ]
}
```

### 2. Get Document

**Endpoint**: `GET /api/v1/documents/{document_id}`

Retrieve all chunks for a specific document.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000"
```

**Response**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "num_chunks": 15,
  "chunks": [
    {
      "chunk_index": 0,
      "content": "First chunk of text...",
      "embedding_length": 384,
      "metadata": {
        "filename": "document.pdf"
      },
      "created_at": "2024-01-08T11:30:00"
    }
  ]
}
```

### 3. Delete Document

**Endpoint**: `DELETE /api/v1/documents/{document_id}`

Delete a document and all its chunks.

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000"
```

**Response**:
```json
{
  "status": "success",
  "message": "Document 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

### 4. Search Documents

**Endpoint**: `POST /api/v1/documents/search`

Search for similar documents using vector similarity.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `query` (required): Search query text
  - `user_id` (optional): User ID to filter by
  - `limit` (optional, default: 5): Maximum number of results

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/search" \
  -F "query=What is machine learning?" \
  -F "limit=5"
```

**Response**:
```json
{
  "query": "What is machine learning?",
  "num_results": 3,
  "results": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_index": 2,
      "content": "Machine learning is a subset of artificial intelligence...",
      "similarity_score": 0.95,
      "metadata": {
        "filename": "document.pdf"
      }
    }
  ]
}
```

### 5. Health Check

**Endpoint**: `GET /health`

Check if the API is running.

**Example**:
```bash
curl -X GET "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy"
}
```

## User and Company Tracking

All document embeddings now include `user_id` and `company_id` for proper ownership tracking and access control:

### Automatic Tracking

When uploading documents, the system automatically:
1. Stores `user_id` with each document chunk (defaults to 0 if not provided)
2. Stores `company_id` with each document chunk (optional, for multi-tenant scenarios)
3. Uses company's embedding model settings when `company_id` is provided

### Benefits

- **Multi-tenant Support**: Different companies can have separate document collections
- **User Isolation**: Documents are associated with specific users
- **Access Control**: Easy to filter documents by user or company
- **Audit Trail**: Complete tracking of document ownership

### Query Examples

```python
from layers.dao import DocumentVectorDAO
from layers.database import SessionLocal

session = SessionLocal()
dao = DocumentVectorDAO(session)

# Get all documents for a user
user_docs = dao.get_vectors_by_user_id(user_id=1)

# Get all documents for a company
company_docs = dao.get_vectors_by_company_id(company_id=1)

# Get documents for a specific user within a company
user_company_docs = dao.get_vectors_by_user_and_company(
    user_id=1,
    company_id=1
)
```

## Company-Specific Embedding Models

Each company can have its own embedding model configuration, allowing different companies to use different embedding strategies:

### Setting Company Embedding Model

Update a company's embedding model settings:

```python
from layers.dao import CompanyDAO
from sqlmodel import Session

# Create a database session
session = SessionLocal()

# Create company DAO
company_dao = CompanyDAO(session)

# Update embedding model for a company
company = company_dao.update_embedding_model(
    company_id=1,
    embedding_model="all-MiniLM-L6-v2",
    embedding_type="local"
)
```

### Using Company-Specific Settings

When uploading documents, specify the `company_id` parameter to use that company's embedding model:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf" \
  -F "company_id=1"  # Uses company 1's embedding model
```

If no `company_id` is provided, the system uses the default embedding model from environment variables.

### Available Embedding Types

#### Local Vectorizer (Default)
- Uses sentence-transformers library
- No API key required
- Runs locally on your machine
- Default model: `all-MiniLM-L6-v2`
- Example: `embedding_type="local", embedding_model="all-MiniLM-L6-v2"`

#### OpenAI Vectorizer
- Uses OpenAI's embedding API
- Requires `OPENAI_API_KEY`
- Default model: `text-embedding-ada-002`
- Higher quality embeddings but costs money
- Example: `embedding_type="openai", embedding_model="text-embedding-ada-002"`

#### HuggingFace Vectorizer
- Uses HuggingFace's inference API
- Requires `HUGGINGFACE_API_KEY`
- Supports various models
- Free tier available
- Example: `embedding_type="huggingface", embedding_model="sentence-transformers/all-MiniLM-L6-v2"`

## Database Schema

### DocumentVector Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| content | Text | Chunk content |
| embedding | Vector(1536) | Embedding vector |
| meta_data | JSONB | Additional metadata |
| document_id | String | Document identifier |
| chunk_index | Integer | Chunk order |
| user_id | Integer | User ID (indexed) |
| company_id | Integer | Company ID (indexed, optional) |
| created_at | Timestamp | Creation time |

### Company Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Company name (indexed) |
| description | String | Company description |
| embedding_model | String | Embedding model name (indexed) |
| embedding_type | String | Embedding type (indexed) |
| llm_model | String | LLM model name (indexed) |
| llm_provider | String | LLM provider type (indexed) |
| llm_endpoint | String | LLM endpoint URL (indexed, optional) |
| llm_api_key | String | LLM API key (optional) |
| llm_temperature | Float | LLM temperature setting |
| llm_max_tokens | Integer | LLM max tokens setting (optional) |
| created_at | Timestamp | Creation time |

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## Troubleshooting

### pgvector Extension Not Found
Make sure pgvector is installed in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### OpenAI API Errors
Verify your `OPENAI_API_KEY` is set correctly in the `.env` file.

### PDF Extraction Issues
Ensure the PDF file is not password-protected or corrupted.

### Local Model Issues
If you encounter issues with local models (Ollama, HuggingFace):
1. Ensure Ollama is running: `curl http://localhost:11434/api/tags`
2. Check if the model is downloaded: `ollama list`
3. Verify you have enough RAM/VRAM for local HuggingFace models
4. Check CUDA availability for GPU acceleration: `python -c "import torch; print(torch.cuda.is_available())"`

For detailed troubleshooting, see [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md).

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
