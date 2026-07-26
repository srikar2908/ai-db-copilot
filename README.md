# AI Database Copilot

AI Database Copilot is a tenant-aware natural-language-to-SQL application. Users authenticate, choose a database connection, ask questions in plain English, review generated SQL, approve or reject it, and inspect execution results and workflow history.

The project is split into a FastAPI/LangGraph backend and a React/Vite frontend. The backend owns authentication, encrypted database connection management, schema extraction, intent extraction, deterministic SQL planning, validation, risk checks, SQL review gates, execution, conversation memory, and audit persistence. The frontend provides the dashboard, connection manager, approval UI, schema explorer, and query history views.

## Repository Layout

```text
ai-db-copilot/
|-- backend/              FastAPI API, LangGraph workflow, SQL engine, platform DB models
|-- frontend/             React 19 + Vite UI served by Nginx in production
|-- docker-compose.yml    Local two-service container setup
|-- render.yaml           Render deployment blueprint
|-- PRODUCTION_AUDIT.md   Production hardening notes and audit record
`-- README.md             Project overview
```

## High-Level Architecture

```mermaid
flowchart LR
    User["User"] --> Browser["React frontend"]
    Browser --> API["FastAPI backend"]

    API --> Auth["JWT auth and RBAC"]
    API --> PlatformDB["Platform database"]
    API --> Graph["LangGraph SQL workflow"]

    PlatformDB --> Users["Users"]
    PlatformDB --> Connections["Encrypted connection refs"]
    PlatformDB --> History["Workflow runs, messages, memory"]

    Graph --> Groq["Groq LLM"]
    Graph --> Schema["Schema extraction"]
    Graph --> SQLGuard["SQL validation, policies, risk"]
    Graph --> TargetDB["Tenant target database"]

    Connections --> TargetDB
    Schema --> TargetDB
    SQLGuard --> TargetDB
```

## Main User Flow

```mermaid
sequenceDiagram
    actor U as User
    participant F as Frontend
    participant A as FastAPI
    participant G as LangGraph
    participant L as Groq LLM
    participant D as Target DB
    participant P as Platform DB

    U->>F: Login and select connection
    F->>A: POST /query
    A->>P: Resolve encrypted connection_ref
    A->>D: Extract schema
    A->>G: Start workflow with tenant, user, schema, prompt
    G->>P: Load conversation memory
    G->>L: Extract SQL intent
    G->>G: Clarify, plan, authorize, validate, classify risk
    G->>P: Save workflow run
    G-->>A: Waiting for SQL review
    A-->>F: Generated SQL and validation metadata
    U->>F: Approve, reject, or edit SQL
    F->>A: POST /approve
    A->>G: Resume checkpoint
    G->>D: Execute approved SQL
    G->>P: Persist result and audit trace
    A-->>F: Execution result
```

## Core Capabilities

- Natural language to SQL using Groq-backed intent extraction.
- Deterministic SQL planning with schema-aware table and column resolution.
- PostgreSQL/Supabase-style connection support, plus helper support for SQLite samples.
- Tenant isolation for users, connections, workflow history, messages, and memory.
- JWT authentication with bcrypt password hashing.
- Role-based access control for analysts, developers, and admins.
- Encrypted database URLs using Fernet.
- SQL parsing and validation with `sqlglot`.
- DDL and unsafe mutation protections.
- Cost and risk classification before execution.
- Human SQL review flow with approve, reject, edit-and-approve, and retry paths.
- Workflow checkpointing through LangGraph.
- Conversation memory and message persistence by thread.
- Query history and audit traces.
- Docker and Render deployment configuration.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router, Axios, Tailwind CSS |
| Backend | FastAPI, LangGraph, SQLAlchemy async, Pydantic, Uvicorn |
| LLM | Groq async client |
| SQL tooling | sqlglot, SQLAlchemy |
| Auth/security | JWT, bcrypt/passlib, Fernet encryption |
| Persistence | PostgreSQL/Supabase for platform data; tenant target databases via connection refs |
| Deployment | Docker, Nginx, Render |
| Tests | pytest, pytest-asyncio |

## Roles

| Role | Backend behavior | Frontend behavior |
| --- | --- | --- |
| `analyst` | Default registration role. Intended for safe read workflows. RBAC allows `SELECT`. | Can use dashboard and view/select connections. Write-style UI actions are visually restricted. |
| `developer` | Can approve reviewed SQL and run non-admin query workflows allowed by policy. | Can edit and approve generated SQL. |
| `admin` | Full connection management and broad workflow visibility within tenant. | Can create tenant database connections and see admin affordances. |

## Backend Workflow

```mermaid
flowchart TD
    Start["POST /query"] --> Memory["load_memory_node"]
    Memory --> Intent["extract_intent_node"]
    Intent --> Clarify["clarification_node"]
    Clarify -->|needs user input| WaitClarify["waiting_for_clarification"]
    Clarify -->|complete| Plan["generate_query_plan_node"]
    Plan --> RBAC["authorize_query_node"]
    RBAC --> Validate["validate_sql_node"]
    Validate -->|failed| Failed["failed"]
    Validate -->|passed| Risk["classify_risk_node"]
    Risk -->|blocked| Failed
    Risk --> Review["request_sql_review_node"]
    Review -->|waiting| WaitReview["waiting_for_sql_review"]
    WaitReview -->|POST /approve| Execute["execute_query_node"]
    Execute -->|success| Done["completed"]
    Execute -->|error| Failed
```

## Local Development

### Prerequisites

- Python 3.11
- Node.js 20+
- PostgreSQL/Supabase-compatible platform database
- Groq API key
- A Fernet encryption key for stored database URLs

### Backend

```powershell
cd backend
python -m venv aisqlhelper
.\aisqlhelper\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
APP_NAME=AI Database Copilot
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/platform_db
ENCRYPTION_KEY=your_fernet_key
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
MAX_QUERY_COST=10000
MAX_ROWS_RETURNED=5000
SCHEMA_CACHE_TTL_SECONDS=300
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT_SECONDS=10
LLM_TEMPERATURE=0
```

Initialize/verify platform tables:

```powershell
python init_platform_db.py
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
```

Create `frontend/.env` for local API routing:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run the UI:

```powershell
npm run dev
```

The Vite app is available at `http://localhost:5173`.

## Docker

Run both services:

```powershell
docker compose up --build
```

The backend is exposed on `http://localhost:8000`. The frontend Nginx container is exposed on `http://localhost:3000`.

## Deployment

`render.yaml` defines two Docker web services:

- `ai-db-copilot-api`, built from `backend/Dockerfile`, health checked at `/health`.
- `ai-db-copilot-frontend`, built from `frontend/Dockerfile`, health checked at `/`.

The backend Dockerfile starts Uvicorn with `${PORT:-8000}` and `${WEB_CONCURRENCY:-1}`. The frontend Dockerfile builds static assets and serves them through Nginx with SPA fallback to `index.html`.

## Testing

Backend tests live under `backend/tests`:

```powershell
cd backend
pytest
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Production Audit](PRODUCTION_AUDIT.md)
