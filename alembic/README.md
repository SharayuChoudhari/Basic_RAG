# Alembic Migration Guide

This directory contains Alembic database migrations for the project.

## Migration Steps

After making changes to the models in `layers/models.py`, follow these steps to create and apply database migrations:

### 1. Generate Migration Script

Since this project uses `uv` for dependency management, you need to run alembic commands through `uv run`. Execute the following command to auto-generate a migration script based on the changes to your models:

```bash
uv run alembic revision --autogenerate -m "Add companies, prompts, and document_vectors tables"
```

This will create a new migration file in the `alembic/versions/` directory.

### 2. Review the Migration

Always review the generated migration script to ensure it accurately reflects your intended changes:

```bash
# Check the generated migration file
cat alembic/versions/<new_migration_file>.py
```

### 3. Apply the Migration

Once you've verified the migration script, apply it to your database using `uv run`:

```bash
uv run alembic upgrade head
```

### 4. Verify the Changes

Connect to your database and verify that the new tables have been created correctly:

```sql
-- List all tables
\dt

-- Check the structure of new tables
\d companies
\d prompts
\d document_vectors
```

## Important Notes

- The migration will create the following new tables:
  - `companies`: For storing company information with a one-to-many relationship to users
  - `prompts`: For storing user prompts with a many-to-one relationship to users
  - `document_vectors`: For storing pgvector embeddings with metadata for RAG

- The existing `users` table will be updated with foreign key relationships to the `companies` and `prompts` tables

- Make sure your database has the pgvector extension installed before applying the migration if you plan to use vector operations

## Troubleshooting

If you encounter any issues during migration:

1. Ensure your database connection is properly configured in `alembic.ini`
2. Check that all required dependencies are installed
3. Verify that the database exists and you have the necessary permissions
