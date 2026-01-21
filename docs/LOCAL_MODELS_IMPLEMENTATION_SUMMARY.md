# Local Models Support - Implementation Summary

## Overview

This document summarizes all changes made to add local model support to the RAG system.

## Changes Made

### 1. Database Models ([`layers/models.py`](../layers/models.py))

Added LLM configuration fields to the [`Company`](../layers/models.py:12) model:

- `llm_model`: Model name (e.g., "llama2", "mistral", "gpt-4")
- `llm_provider`: Provider type (openai, anthropic, google, huggingface, ollama, local_hf)
- `llm_endpoint`: Endpoint URL for local models (e.g., "http://localhost:11434")
- `llm_api_key`: API key for cloud providers
- `llm_temperature`: Temperature for generation (default: 0.7)
- `llm_max_tokens`: Max tokens for generation

### 2. Schemas ([`layers/schemas.py`](../layers/schemas.py))

Updated schemas to include LLM configuration:

- [`CompanyCreate`](../layers/schemas.py:9): Added LLM fields with defaults
- [`CompanyUpdate`](../layers/schemas.py:17): Added optional LLM fields
- [`CompanyResponse`](../layers/schemas.py:25): Added LLM fields to response
- [`UserCompanyResponse`](../layers/schemas.py:60): Added LLM fields to user's company response

### 3. Data Access Object ([`layers/dao/companies_dao.py`](../layers/dao/companies_dao.py))

Added new methods to [`CompanyDAO`](../layers/dao/companies_dao.py:7):

- [`get_llm_config(company_id)`](../layers/dao/companies_dao.py:83): Retrieve LLM configuration for a company
- [`update_llm_config(company_id, llm_config)`](../layers/dao/companies_dao.py:95): Update LLM configuration for a company

### 4. Chat Service ([`services/chat_messages.py`](../services/chat_messages.py))

Enhanced [`ChatMessageService`](../services/chat_messages.py:40) with local model support:

- Updated [`ChatState`](../services/chat_messages.py:29) to include `llm_config` field
- Enhanced [`_get_llm()`](../services/chat_messages.py:104) method to support:
  - **Ollama**: Local models via Ollama API
  - **Local HuggingFace**: Local HuggingFace models with transformers
  - **Cloud providers**: OpenAI, Anthropic, Google, HuggingFace Hub
- Updated [`generate_node()`](../services/chat_messages.py:64) to use LLM configuration
- Updated [`process_query()`](../services/chat_messages.py:198) to retrieve and use company's LLM configuration

### 5. Controllers

#### Companies Controller ([`controllers/companies.py`](../controllers/companies.py))

- Updated [`create_company()`](../controllers/companies.py:15) to accept LLM configuration
- Updated [`get_all_companies()`](../controllers/companies.py:55) to return LLM fields
- Updated [`get_company()`](../controllers/companies.py:90) to return LLM fields
- Updated [`update_company()`](../controllers/companies.py:132) to handle LLM configuration updates
- Updated [`update_company_embedding_model()`](../controllers/companies.py:226) to return LLM fields
- Added new endpoint [`update_company_llm_config()`](../controllers/companies.py:275) for updating LLM settings

#### Users Controller ([`controllers/users.py`](../controllers/users.py))

- Updated [`get_user_company()`](../controllers/users.py:260) to return LLM configuration

### 6. Dependencies ([`pyproject.toml`](../pyproject.toml))

Added new dependencies:

```toml
# LangChain and LLM providers
"langchain>=0.1.0",
"langchain-openai>=0.0.5",
"langchain-anthropic>=0.1.0",
"langchain-google-genai>=1.0.0",
"langchain-community>=0.0.20",
"langgraph>=0.0.20",
# Local model support
"ollama>=0.1.0",
"transformers>=4.36.0",
"torch>=2.1.0",
```

### 7. Database Migration ([`alembic/versions/add_llm_configuration_to_companies.py`](../alembic/versions/add_llm_configuration_to_companies.py))

Created new migration to add LLM configuration columns to the `companies` table:

- Added columns: `llm_model`, `llm_provider`, `llm_endpoint`, `llm_api_key`, `llm_temperature`, `llm_max_tokens`
- Created indexes for: `llm_model`, `llm_provider`, `llm_endpoint`
- Includes upgrade and downgrade functions

### 8. Documentation

#### Main README ([`README.md`](../README.md))

- Updated Features section to highlight local LLM support
- Updated Prerequisites to include Ollama and GPU requirements
- Updated Configuration section with LLM environment variables
- Added new endpoint documentation for LLM configuration
- Updated database schema documentation
- Added troubleshooting section for local models

#### Local Models Documentation ([`docs/LOCAL_MODELS.md`](LOCAL_MODELS.md))

Created comprehensive documentation covering:

- Overview of supported LLM providers
- Database schema for LLM configuration
- API endpoints for LLM configuration
- Setup guides for Ollama and local HuggingFace models
- Usage examples with code samples
- Environment variable configuration
- Performance considerations
- Troubleshooting guide
- API reference

## Supported LLM Providers

### Cloud Providers
- **OpenAI**: GPT-4, GPT-3.5-turbo, etc.
- **Anthropic**: Claude 3 Sonnet, Claude 3 Opus, etc.
- **Google**: Gemini Pro, Gemini Pro Vision, etc.
- **HuggingFace Hub**: Any model available on HuggingFace Hub

### Local Providers
- **Ollama**: Run local models via Ollama (llama2, mistral, codellama, etc.)
- **Local HuggingFace**: Run HuggingFace models locally (requires model download)

## API Endpoints

### New Endpoint

```
PUT /api/v1/companies/{company_id}/llm-config
```

Query Parameters:
- `llm_model` (required): Model name
- `llm_provider` (required): Provider type
- `llm_endpoint` (optional): Endpoint URL for local models
- `llm_api_key` (optional): API key for cloud providers
- `llm_temperature` (optional, default: 0.7): Temperature
- `llm_max_tokens` (optional): Max tokens

### Updated Endpoints

All company-related endpoints now include LLM configuration in responses:
- `POST /api/v1/companies/`
- `GET /api/v1/companies/`
- `GET /api/v1/companies/{company_id}`
- `PUT /api/v1/companies/{company_id}`
- `PUT /api/v1/companies/{company_id}/embedding-model`
- `GET /api/v1/users/{user_id}/company`

## Usage Example

### Setting Up Ollama

```bash
# Install and start Ollama
brew install ollama
ollama serve

# Pull a model
ollama pull llama2

# Configure company
curl -X PUT "http://localhost:8000/api/v1/companies/{company_id}/llm-config" \
  "?llm_model=llama2&llm_provider=ollama&llm_endpoint=http://localhost:11434"

# Send a chat query
curl -X POST "http://localhost:8000/api/v1/chat-messages/query" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "{chat_id}", "query": "Hello!"}'
```

### Setting Up Local HuggingFace

```bash
# Configure company
curl -X PUT "http://localhost:8000/api/v1/companies/{company_id}/llm-config" \
  "?llm_model=gpt2&llm_provider=local_hf&llm_temperature=0.8"

# Send a chat query
curl -X POST "http://localhost:8000/api/v1/chat-messages/query" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "{chat_id}", "query": "Tell me a joke"}'
```

## Migration Instructions

To apply the database changes:

```bash
# Run the migration
alembic upgrade head

# Verify the migration
alembic current
```

If you need to rollback:

```bash
alembic downgrade -1
```

## Testing

To test the implementation:

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```

4. **Test with Ollama**:
   ```bash
   # Ensure Ollama is running
   ollama serve
   
   # Create a company with Ollama configuration
   curl -X POST "http://localhost:8000/api/v1/companies/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Company",
       "llm_model": "llama2",
       "llm_provider": "ollama",
       "llm_endpoint": "http://localhost:11434"
     }'
   
   # Send a chat query
   curl -X POST "http://localhost:8000/api/v1/chat-messages/query" \
     -H "Content-Type: application/json" \
     -d '{"chat_id": "{chat_id}", "query": "Hello!"}'
   ```

## Benefits

1. **Cost Savings**: Use local models instead of paid cloud APIs
2. **Data Privacy**: Keep data on-premises with local models
3. **Flexibility**: Choose from multiple providers per company
4. **Easy Setup**: Simple configuration via API
5. **Backward Compatible**: Existing cloud providers still work

## Future Enhancements

Potential improvements:
- Support for more local model providers (LM Studio, LocalAI)
- Model caching and preloading
- Streaming responses for local models
- Model performance monitoring
- Automatic model selection based on query complexity
- Support for multi-modal models

## Files Modified

1. [`layers/models.py`](../layers/models.py) - Added LLM configuration fields
2. [`layers/schemas.py`](../layers/schemas.py) - Updated schemas
3. [`layers/dao/companies_dao.py`](../layers/dao/companies_dao.py) - Added LLM config methods
4. [`services/chat_messages.py`](../services/chat_messages.py) - Enhanced LLM support
5. [`controllers/companies.py`](../controllers/companies.py) - Added LLM config endpoint
6. [`controllers/users.py`](../controllers/users.py) - Updated user company response
7. [`pyproject.toml`](../pyproject.toml) - Added dependencies
8. [`README.md`](../README.md) - Updated documentation
9. [`alembic/versions/add_llm_configuration_to_companies.py`](../alembic/versions/add_llm_configuration_to_companies.py) - New migration

## Files Created

1. [`docs/LOCAL_MODELS.md`](LOCAL_MODELS.md) - Comprehensive local models documentation
2. [`docs/LOCAL_MODELS_IMPLEMENTATION_SUMMARY.md`](LOCAL_MODELS_IMPLEMENTATION_SUMMARY.md) - This summary document
