# Homebase API

The FastAPI service for Homebase. See the repository root README for setup and run instructions.

## Coffee suggestions integration tests

Create a separate PostgreSQL database named `homebase_test` (or another name ending in `_test`) and set `TEST_DATABASE_URL` to its SQLAlchemy URL. For example, in PowerShell:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://homebase:homebase@localhost:5432/homebase_test'
uv run pytest
```

The test fixture applies Alembic migrations to that database and rolls back each test's data. It refuses a URL for the normal application database. Without `TEST_DATABASE_URL`, database integration tests are skipped.
