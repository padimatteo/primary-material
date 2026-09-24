# Homebase

A small personal application that can grow into separate modules for coffee recipes, running, journaling, web crawlers, and whatever comes next.

## Stack

- **API:** Python 3.12+ with FastAPI
- **Frontend:** React, TypeScript, and Vite
- **Database:** PostgreSQL 18 in Docker Compose
- **Python packages:** `uv`

The API and frontend run directly on your machine for fast reloads. PostgreSQL runs in a container and stores its data in a named Docker volume.

## Project layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- config.py       # Environment-backed settings
|   |   |-- database.py     # SQLAlchemy engine
|   |   |-- main.py         # FastAPI application
|   |   `-- routes.py       # Hello and health endpoints
|   |-- tests/
|   `-- pyproject.toml
|-- frontend/
|   |-- src/
|   `-- vite.config.ts      # Includes the /api development proxy
|-- compose.yaml
`-- .env.example
```

## Prerequisites

Install these once:

- [Docker Desktop](https://docs.docker.com/desktop/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js](https://nodejs.org/) (the current Vite release requires a recent version)

Node is already available on this machine. Python does not need to be installed separately when you use `uv`; it can install the requested Python version for the project.

## First-time setup

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d db

Set-Location backend
uv sync
Set-Location ..\frontend
npm install
```

The `.env` file is ignored by Git. The checked-in defaults are only development credentials; use proper secrets in any deployed environment.

## Run the app

Use two terminals after the database is running.

Terminal 1 — API:

```powershell
Set-Location backend
uv run alembic upgrade head # runs migrations
uv run fastapi dev
```

Terminal 2 — frontend:

```powershell
Set-Location frontend
npm run dev
```

Then open:

- App: <http://localhost:5173>
- Hello endpoint: <http://localhost:8000/api/hello>
- Database health: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>

## Check the scaffold

```powershell
# Backend
Set-Location backend
uv run pytest
uv run ruff check .

# Frontend
Set-Location ..\frontend
npm run lint
npm run build
```

## Useful database commands

```powershell
# Follow database logs
docker compose logs -f db

# Open psql inside the container
docker compose exec db psql -U homebase -d homebase

# Stop services but retain database data
docker compose down

# Stop services and delete local database data
docker compose down --volumes
```

## A sensible next slice

Build one vertical feature end to end—coffee recipes would be a good first one. Add a database model and Alembic migration, API routes, then one small React screen. This will expose which shared patterns the app actually needs before introducing authentication, queues, RAG infrastructure, or crawler scheduling.
