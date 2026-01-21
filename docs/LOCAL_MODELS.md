# Local Models Support

This document describes how to configure and use local LLM models with the RAG system.

## Overview

The RAG system now supports multiple LLM providers, including local models. You can configure different LLM providers at the company level, allowing each company to use their preferred model.

## Supported LLM Providers

### Cloud Providers
- **OpenAI**: `gpt-4`, `gpt-3.5-turbo`, etc.
- **Anthropic**: `claude-3-sonnet-20240229`, `claude-3-opus-20240229`, etc.
- **Google**: `gemini-pro`, `gemini-pro-vision`, etc.
- **HuggingFace Hub**: Any model available on HuggingFace Hub

### Local Providers
- **Ollama**: Run local models via Ollama (e.g., `llama2`, `mistral`, `codellama`)
- **Local HuggingFace**: Run HuggingFace models locally (requires model download)

## Configuration

### Database Schema

The `companies` table now includes the following LLM configuration fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `llm_model` | String | `gpt-4` | Model name (e.g., "llama2", "mistral", "gpt-4") |
| `llm_provider` | String | `openai` | Provider: `openai`, `anthropic`, `google`, `huggingface`, `ollama`, `local_hf` |
| `llm_endpoint` | String | `null` | Endpoint URL for local models (e.g., "http://localhost:11434") |
| `llm_api_key` | String | `null` | API key for cloud providers |
| `llm_temperature` | Float | `0.7` | Temperature for generation |
| `llm_max_tokens` | Integer | `null` | Max tokens for generation |

### API Endpoints

#### Create Company with LLM Configuration

```bash
POST /api/v1/companies/
Content-Type: application/json

{
  "name": "My Company",
  "description": "Company description",
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_type": "local",
  "llm_model": "llama2",
  "llm_provider": "ollama",
  "llm_endpoint": "http://localhost:11434",
  "llm_temperature": 0.7,
  "llm_max_tokens": 1000
}
```

#### Update Company LLM Configuration

```bash
PUT /api/v1/companies/{company_id}/llm-config?llm_model=llama2&llm_provider=ollama&llm_endpoint=http://localhost:11434&llm_temperature=0.7&llm_max_tokens=1000
```

Or via the general update endpoint:

```bash
PUT /api/v1/companies/{company_id}
Content-Type: application/json

{
  "llm_model": "mistral",
  "llm_provider": "ollama",
  "llm_endpoint": "http://localhost:11434",
  "llm_temperature": 0.8,
  "llm_max_tokens": 2000
}
```

## Setting Up Local Models

### Ollama Setup

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Windows
   # Download from https://ollama.com/download
   ```

2. **Start Ollama Server**:
   ```bash
   ollama serve
   ```

3. **Pull a Model**:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ollama pull codellama
   ```

4. **Configure Company**:
   ```bash
   PUT /api/v1/companies/{company_id}/llm-config
   ?llm_model=llama2
   &llm_provider=ollama
   &llm_endpoint=http://localhost:11434
   &llm_temperature=0.7
   ```

5. **Test the Configuration**:
   ```bash
   POST /api/v1/chat-messages/query
   Content-Type: application/json

   {
     "chat_id": "{chat_id}",
     "query": "Hello, how are you?",
     "use_retrieval": false
   }
   ```

### Local HuggingFace Setup

1. **Install Dependencies**:
   ```bash
   pip install transformers torch
   ```

2. **Download a Model** (optional, will download on first use):
   ```python
   from transformers import AutoTokenizer, AutoModelForCausalLM
   
   # Download model
   tokenizer = AutoTokenizer.from_pretrained("gpt2")
   model = AutoModelForCausalLM.from_pretrained("gpt2")
   ```

3. **Configure Company**:
   ```bash
   PUT /api/v1/companies/{company_id}/llm-config
   ?llm_model=gpt2
   &llm_provider=local_hf
   &llm_temperature=0.7
   &llm_max_tokens=500
   ```

4. **Test the Configuration**:
   ```bash
   POST /api/v1/chat-messages/query
   Content-Type: application/json

   {
     "chat_id": "{chat_id}",
     "query": "Hello, how are you?",
     "use_retrieval": false
   }
   ```

## Usage Examples

### Using Ollama with Llama2

```python
import requests

# Update company configuration
response = requests.put(
    "http://localhost:8000/api/v1/companies/{company_id}/llm-config",
    params={
        "llm_model": "llama2",
        "llm_provider": "ollama",
        "llm_endpoint": "http://localhost:11434",
        "llm_temperature": 0.7,
        "llm_max_tokens": 1000
    }
)

# Send a chat query
response = requests.post(
    "http://localhost:8000/api/v1/chat-messages/query",
    json={
        "chat_id": "{chat_id}",
        "query": "What is the capital of France?",
        "use_retrieval": True,
        "top_k": 5
    }
)

print(response.json())
```

### Using Local HuggingFace Model

```python
import requests

# Update company configuration
response = requests.put(
    "http://localhost:8000/api/v1/companies/{company_id}/llm-config",
    params={
        "llm_model": "gpt2",
        "llm_provider": "local_hf",
        "llm_temperature": 0.8,
        "llm_max_tokens": 500
    }
)

# Send a chat query
response = requests.post(
    "http://localhost:8000/api/v1/chat-messages/query",
    json={
        "chat_id": "{chat_id}",
        "query": "Tell me a joke",
        "use_retrieval": False
    }
)

print(response.json())
```

### Overriding Company Configuration per Query

You can override the company's LLM configuration for individual queries:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat-messages/query",
    json={
        "chat_id": "{chat_id}",
        "query": "What is machine learning?",
        "use_retrieval": True,
        "top_k": 5,
        "llm_model": "mistral",  # Override company default
        "llm_provider": "ollama"  # Override company default
    }
)

print(response.json())
```

## Environment Variables

For cloud providers, you can set API keys via environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google
export GOOGLE_API_KEY="your-google-api-key"

# HuggingFace Hub
export HUGGINGFACEHUB_API_TOKEN="your-huggingface-token"
```

Or you can store API keys in the company's `llm_api_key` field.

## Performance Considerations

### Ollama
- **Pros**: Easy to set up, good performance, many models available
- **Cons**: Requires running Ollama server, limited to models available on Ollama
- **Recommended for**: Production use, ease of setup

### Local HuggingFace
- **Pros**: Full control over models, can use any HuggingFace model
- **Cons**: Requires more setup, higher memory usage, slower inference
- **Recommended for**: Research, custom models, fine-tuned models

### Cloud Providers
- **Pros**: Best performance, no local resources needed
- **Cons**: API costs, data privacy concerns
- **Recommended for**: Production when cost is not a concern

## Troubleshooting

### Ollama Connection Issues

If you get connection errors when using Ollama:

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Verify the endpoint URL in your company configuration

3. Check Ollama logs for errors

### Local HuggingFace Model Issues

If you get errors loading local HuggingFace models:

1. Ensure you have enough RAM/VRAM for the model
2. Check if the model is downloaded:
   ```python
   from transformers import AutoTokenizer
   tokenizer = AutoTokenizer.from_pretrained("gpt2")
   ```

3. For GPU support, ensure CUDA is properly installed:
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

### Migration Issues

If you encounter issues after adding the LLM configuration fields:

1. Run the migration:
   ```bash
   alembic upgrade head
   ```

2. Check the migration status:
   ```bash
   alembic current
   ```

3. If needed, rollback and re-run:
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

## API Reference

### Company Response Schema

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "embedding_model": "string",
  "embedding_type": "string",
  "llm_model": "string",
  "llm_provider": "string",
  "llm_endpoint": "string | null",
  "llm_temperature": "number",
  "llm_max_tokens": "number | null",
  "created_at": "string (ISO 8601)"
}
```

### Chat Query Response Schema

```json
{
  "message_id": "uuid",
  "chat_id": "uuid",
  "query": "string",
  "response": "string",
  "context_documents": [
    {
      "document_id": "uuid",
      "chunk_index": "number",
      "content": "string",
      "metadata": "object | null"
    }
  ],
  "created_at": "string (ISO 8601)",
  "llm_model": "string",
  "llm_provider": "string"
}
```

## Future Enhancements

Potential future improvements:

1. Support for more local model providers (e.g., LM Studio, LocalAI)
2. Model caching and preloading
3. Streaming responses for local models
4. Model performance monitoring
5. Automatic model selection based on query complexity
6. Support for multi-modal models
