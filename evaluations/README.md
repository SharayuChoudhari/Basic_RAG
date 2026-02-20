# RAGAS Evaluation Pipeline

A modular evaluation system for RAG (Retrieval-Augmented Generation) systems using RAGAS metrics. This pipeline supports both batch evaluation and real-time per-query evaluation modes.

## Features

- **RAGAS Metrics**: Faithfulness, Answer Relevance, Context Precision
- **Batch Evaluation**: Evaluate multiple queries from ChatMessage database
- **Per-Query Evaluation**: Evaluate single queries for real-time integration
- **Company-Scoped**: Evaluations are scoped to companies for multi-tenant systems
- **Dual Storage**: Results stored in both PostgreSQL database and JSON files
- **Configurable**: Model selection, thresholds, batch sizes via config

## Quick Start

### Prerequisites

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Run Evaluation

```bash
# Evaluate all queries for a company
python -m evaluations.run_evaluations --company-id <uuid>

# Preview what would be evaluated
python -m evaluations.run_evaluations --preview --company-id <uuid>

# Dry run (no database save)
python -m evaluations.run_evaluations --company-id <uuid> --dry-run
```

## CLI Usage

### Batch Evaluation

```bash
# Basic usage - evaluates last 7 days by default
python -m evaluations.run_evaluations --company-id <uuid>

# Evaluate last 30 days
python -m evaluations.run_evaluations --company-id <uuid> --days 30

# Evaluate all time (no date filter)
python -m evaluations.run_evaluations --company-id <uuid> --days 0

# Filter by specific chats
python -m evaluations.run_evaluations --company-id <uuid> --chat-ids <uuid1> <uuid2>

# Filter by explicit date range (overrides --days)
python -m evaluations.run_evaluations --company-id <uuid> --from-date 2024-01-01 --to-date 2024-01-31

# Limit number of queries
python -m evaluations.run_evaluations --company-id <uuid> --limit 100

# Custom model
python -m evaluations.run_evaluations --company-id <uuid> --model gpt-4-turbo
```

### Single Query Evaluation

```bash
# Evaluate a single query
python -m evaluations.run_evaluations --single \
  --question "What is the revenue?" \
  --answer "The revenue was $10M in Q1." \
  --contexts "Revenue was $10M in Q1." "Q1 financial report shows growth."
```

### Preview Mode

```bash
# Preview evaluation scope without running
python -m evaluations.run_evaluations --preview --company-id <uuid>
```

## Module Reference

### Configuration (`config.py`)

```python
from evaluations.config import EvaluationConfig

# Default configuration from environment
config = EvaluationConfig.from_env()

# Custom configuration
config = EvaluationConfig(
    llm_model="gpt-4",
    metrics=["faithfulness", "answer_relevance", "context_precision"],
    thresholds={"faithfulness": 0.7, "answer_relevance": 0.7},
    batch_size=10,
    output_dir="evaluations/results",
)

# Validate configuration
errors = config.validate()
```

### Single Query Evaluator (`single_eval.py`)

```python
from evaluations.single_eval import SingleQueryEvaluator

# Create evaluator
evaluator = SingleQueryEvaluator.from_env()

# Evaluate a single query
result = evaluator.evaluate_single(
    question="What is the revenue?",
    retrieved_contexts=["Revenue was $10M in Q1."],
    answer="The revenue was $10 million in Q1.",
)

# Access scores
print(f"Faithfulness: {result.faithfulness_score}")
print(f"Answer Relevance: {result.answer_relevance_score}")
print(f"Context Precision: {result.context_precision_score}")
print(f"Overall Score: {result.overall_score}")

# Check against thresholds
pass_fail = evaluator.get_pass_fail_summary(result)
```

### Batch Runner (`batch_runner.py`)

```python
from sqlmodel import Session
from evaluations.batch_runner import BatchEvaluationRunner
from evaluations.config import EvaluationConfig

# Create runner
runner = BatchEvaluationRunner(session, config)

# Run evaluation for last 7 days (default)
result = runner.run_evaluation(
    company_id=company_uuid,
    days=7,
)

# Run evaluation for last 30 days
result = runner.run_evaluation(
    company_id=company_uuid,
    days=30,
)

# Run evaluation for all time
result = runner.run_evaluation(
    company_id=company_uuid,
    days=0,  # or days=None
)

# Run evaluation with explicit date range
result = runner.run_evaluation(
    company_id=company_uuid,
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    limit=100,
)

# Get evaluation history
history = runner.get_evaluation_history(company_uuid, limit=10)

# Get job details
details = runner.get_job_details(job_uuid)
```

### Dataset Loader (`dataset_loader.py`)

```python
from evaluations.dataset_loader import DatasetLoader

# Create loader
loader = DatasetLoader(session, company_id=company_uuid)

# Load messages for evaluation
inputs = loader.load_messages(
    chat_ids=[chat_uuid],
    date_range=(start_date, end_date),
    limit=100,
)

# Load single message
input_data = loader.load_single_message(message_uuid)

# Get count
count = loader.get_message_count(chat_ids=[chat_uuid])
```

### Metrics Store (`metrics_store.py`)

```python
from evaluations.metrics_store import MetricsStore

# Create store
store = MetricsStore.from_config(session, config)

# Create job
job = store.create_job(company_id=company_uuid)

# Save result
store.save_single_result(job.id, result)

# Compute and save summary
summary = store.compute_aggregated_summary(results)
store.save_job_summary(job.id, summary)

# Save to JSON
filepath = store.save_to_json(job.id, results, summary)

# Query history
history = store.get_company_evaluation_history(company_uuid)
```

## Database Schema

### EvaluationJob

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| company_id | UUID | FK to companies.id |
| status | str | pending, running, completed, failed |
| total_queries | int | Number of queries evaluated |
| avg_faithfulness | float | Average faithfulness score |
| avg_answer_relevance | float | Average answer relevance score |
| avg_context_precision | float | Average context precision score |
| overall_score | float | Weighted average of all metrics |
| started_at | datetime | When evaluation started |
| completed_at | datetime | When evaluation completed |
| error_message | str | Error details if failed |
| config_snapshot | JSONB | Configuration used |
| created_at | datetime | Record creation timestamp |

### EvaluationResult

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| job_id | UUID | FK to evaluation_jobs.id (nullable) |
| chat_message_id | UUID | FK to chat_messages.id |
| company_id | UUID | FK to companies.id |
| question | str | The user query |
| retrieved_contexts | JSONB | List of retrieved documents |
| answer | str | The generated response |
| faithfulness_score | float | Faithfulness metric (0-1) |
| answer_relevance_score | float | Answer relevance metric (0-1) |
| context_precision_score | float | Context precision metric (0-1) |
| overall_score | float | Average of all metrics |
| evaluation_metadata | JSONB | Additional metadata |
| created_at | datetime | Record creation timestamp |

## Output Format

### JSON Output

Results are saved to `evaluations/results/` with the following structure:

```json
{
  "job_id": "uuid",
  "summary": {
    "job_id": "uuid",
    "company_id": "uuid",
    "total_queries": 100,
    "faithfulness": {
      "mean": 0.82,
      "median": 0.85,
      "std": 0.12,
      "min": 0.45,
      "max": 0.98,
      "distribution": {
        "0.0-0.2": 2,
        "0.2-0.4": 5,
        "0.4-0.6": 10,
        "0.6-0.8": 30,
        "0.8-1.0": 53
      }
    },
    "answer_relevance": {...},
    "context_precision": {...},
    "overall_score": 0.82
  },
  "results": [
    {
      "id": "uuid",
      "question": "What is the revenue?",
      "retrieved_contexts": ["..."],
      "answer": "The revenue was...",
      "faithfulness_score": 0.85,
      "answer_relevance_score": 0.92,
      "context_precision_score": 0.78,
      "overall_score": 0.85
    }
  ]
}
```

## RAGAS Metrics

### Faithfulness

Measures how faithful the answer is to the retrieved context. A high score indicates the answer is well-grounded in the provided documents.

**Formula**: Claims in answer / Claims supported by context

### Answer Relevance

Measures how relevant the answer is to the original question. A high score indicates the answer directly addresses the user's query.

**Formula**: Based on LLM evaluation of answer-question alignment

### Context Precision

Measures the precision of retrieved context. A high score indicates the retrieved documents are relevant to the question.

**Formula**: Relevant chunks / Total retrieved chunks

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key | Required |
| EVAL_LLM_MODEL | LLM model for evaluation | gpt-4 |
| EVAL_LLM_PROVIDER | LLM provider | openai |
| EVAL_BATCH_SIZE | Batch size for processing | 10 |
| EVAL_OUTPUT_DIR | Output directory for JSON | evaluations/results |
| EVAL_SAVE_TO_DB | Save results to database | true |
| EVAL_SAVE_TO_JSON | Save results to JSON | true |

## Future Integration

### Real-time Evaluation

The `SingleQueryEvaluator` can be integrated directly into the chat flow:

```python
# In services/chat_messages.py
from evaluations.single_eval import SingleQueryEvaluator

async def process_query(self, query_request: ChatQueryRequest):
    # ... existing response generation ...
    
    # Trigger evaluation (can be background task)
    evaluator = SingleQueryEvaluator.from_env()
    eval_result = await evaluator.evaluate_single_async(
        question=query_request.query,
        retrieved_contexts=[doc["content"] for doc in context_documents],
        answer=response,
    )
    
    # Store result
    metrics_store.save_single_result(job_id=None, result=eval_result)
```

### Dashboard Integration

Query evaluation history for dashboards:

```python
# Get latest evaluation for company
latest_job = metrics_store.get_latest_job(company_id)

# Get trend data
history = metrics_store.get_company_evaluation_history(
    company_id, 
    limit=30
)
```

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY is required"**
   - Set the environment variable: `export OPENAI_API_KEY=your_key`

2. **"No messages to evaluate"**
   - Ensure ChatMessage records have both `response` and `context_document`
   - Check the company_id filter matches your data

3. **"Migration failed"**
   - Run `alembic upgrade head` to apply the evaluation tables migration

4. **Slow evaluation**
   - Reduce batch size: `--batch-size 5`
   - Use a faster model: `--model gpt-3.5-turbo`

## Architecture

See [plans/evaluation_pipeline_architecture.md](../plans/evaluation_pipeline_architecture.md) for detailed architecture documentation.
