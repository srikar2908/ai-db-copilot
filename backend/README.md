# AI Database Copilot Backend

The backend is a FastAPI service that turns natural-language requests into reviewed, validated, tenant-scoped SQL workflows. It combines Groq LLM calls, deterministic planning, LangGraph orchestration, SQL validation, RBAC, encrypted database connections, query execution, and audit persistence.

## Responsibilities

- Register and authenticate platform users.
- Enforce tenant identity and role-based access control.
- Store target database connections as encrypted URLs.
- Extract target database schema for SQL generation and validation.
- Convert user prompts into SQL intent with Groq.
- Resolve schema-aware query plans deterministically.
- Build, normalize, explain, and validate SQL.
- Block unsafe DDL, suspicious SQL patterns, and mutations without `WHERE`.
- Classify query risk and estimate query cost.
- Pause every generated SQL workflow for human review.
- Resume approved or edited workflows from LangGraph checkpoints.
- Execute approved SQL against the selected tenant connection.
- Persist workflow runs, messages, and conversation memory.

## Architecture

```mermaid
flowchart LR
    Client["React client"] --> API["FastAPI app.main"]

    API --> Routers["API routers"]
    Routers --> AuthRouter["auth.py"]
    Routers --> ConnRouter["connections.py"]
    Routers --> HistRouter["history.py"]
    Routers --> ResumeRouter["resume.py"]
    Routers --> ApprovalRouter["routes/approval.py"]

    API --> Security["security/"]
    Security --> JWT["JWT verification"]
    Security --> Passwords["bcrypt hashing"]
    Security --> Encryption["Fernet URL encryption"]

    API --> Platform["platform/"]
    Platform --> PlatformDB["SQLAlchemy async platform DB"]

    API --> Graph["core/graph/"]
    Graph --> Nodes["workflow nodes"]
    Nodes --> Intent["core/intent.py"]
    Nodes --> Planner["core/planner.py"]
    Nodes --> SQL["core/sql/"]
    Nodes --> Policies["core/policies/"]
    Nodes --> Cost["core/cost/"]

    Graph --> TargetDB["Tenant target DB"]
    SQL --> TargetDB
```

## Request Workflow

```mermaid
stateDiagram-v2
    [*] --> running
    running --> waiting_for_clarification: ambiguous intent
    waiting_for_clarification --> running: /workflow/resume
    running --> waiting_for_sql_review: SQL generated and validated
    waiting_for_sql_review --> approved: /approve
    waiting_for_sql_review --> rejected: /reject
    approved --> completed: execution succeeds
    approved --> failed: execution fails
    running --> failed: validation, RBAC, or policy failure
    rejected --> [*]
    completed --> [*]
    failed --> [*]
```

## Directory Guide

```text
backend/
|-- app/
|   |-- main.py                 FastAPI app, CORS, routers, /query, /schema
|   |-- config.py               Pydantic settings from .env
|   |-- api/                    Auth, connections, history, resume routers
|   |-- api/routes/approval.py  Approve, reject, edit-and-approve workflow APIs
|   |-- core/
|   |   |-- graph/              LangGraph state machine, routes, nodes, checkpointing
|   |   |-- sql/                SQL builder, parser, validator, reviewer, executor
|   |   |-- schema/             Schema extraction and semantic resolution
|   |   |-- policies/           RBAC and SQL policy checks
|   |   |-- clarification/      Ambiguity detection and clarification resolution
|   |   |-- cost/               Query cost analysis
|   |   |-- intent.py           LLM-backed intent extraction
|   |   `-- planner.py          Deterministic query plan generation
|   |-- db/                     Connection URL resolution and helpers
|   |-- models/                 Pydantic workflow and API models
|   |-- platform/               SQLAlchemy models, repositories, users, memory
|   |-- security/               JWT, password hashing, encryption, dependencies
|   `-- utils/                  Time helpers
|-- tests/                      pytest tests
|-- migrations/                 Production hardening SQL
|-- Dockerfile
|-- requirements.txt
|-- init_platform_db.py
`-- init_db.py                 Small SQLite sample database helper
```

## Key API Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | No | Basic service status message |
| `GET` | `/health` | No | Health check endpoint |
| `POST` | `/register` | No | Create a platform user, defaulting to `analyst` |
| `POST` | `/login` | No | Authenticate and return JWT/user payload |
| `GET` | `/connections` | Yes | List visible tenant connections |
| `POST` | `/connections` | Yes, admin | Create encrypted tenant database connection |
| `GET` | `/schema?connection_ref=...` | Yes | Extract schema from selected target connection |
| `POST` | `/query` | Yes | Start natural-language-to-SQL workflow |
| `POST` | `/approve` | Yes, developer/admin | Approve generated SQL or route edited SQL for review |
| `POST` | `/edit-and-approve` | Yes, developer/admin | Validate edited SQL, approve, and resume execution |
| `POST` | `/reject` | Yes | Reject a waiting SQL workflow |
| `POST` | `/workflow/resume` | Yes | Resume a workflow waiting for clarification |
| `GET` | `/history` | Yes | Latest workflow runs for tenant/user |
| `GET` | `/threads` | Yes | List workflow threads |
| `GET` | `/thread/{thread_id}` | Yes | Get a workflow run by thread |
| `GET` | `/thread/{thread_id}/messages` | Yes | Get persisted thread messages |
| `POST` | `/test-policy` | No | Debug SQL policy evaluation |

## Platform Data Model

```mermaid
erDiagram
    PLATFORM_USERS {
        int id PK
        string tenant_id
        string email
        text hashed_password
        string full_name
        string role
        datetime created_at
    }

    DATABASE_CONNECTIONS {
        int id PK
        string tenant_id
        int owner_user_id
        string connection_ref
        text encrypted_database_url
        string database_type
        datetime created_at
    }

    WORKFLOW_RUNS {
        string thread_id PK
        string tenant_id
        string user_id
        string connection_ref
        text user_prompt
        text generated_sql
        string approval_status
        string risk_level
        string execution_status
        json validation_result
        json execution_result
        json node_trace
        json errors
    }

    CONVERSATION_MEMORY {
        int id PK
        string thread_id
        string tenant_id
        string user_id
        string active_table
        text selected_columns
        text active_filters
        text last_generated_sql
        text last_user_prompt
    }

    CONVERSATION_MESSAGES {
        string id PK
        string thread_id
        string tenant_id
        string user_id
        string role
        json content
        datetime created_at
    }

    PLATFORM_USERS ||--o{ DATABASE_CONNECTIONS : owns
    PLATFORM_USERS ||--o{ WORKFLOW_RUNS : runs
    WORKFLOW_RUNS ||--o{ CONVERSATION_MESSAGES : records
    WORKFLOW_RUNS ||--o| CONVERSATION_MEMORY : remembers
```

## Environment Variables

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

Generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Local Setup

```powershell
cd backend
python -m venv aisqlhelper
.\aisqlhelper\Scripts\activate
pip install -r requirements.txt
python init_platform_db.py
uvicorn app.main:app --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Query Lifecycle Details

1. `/query` receives `thread_id`, `connection_ref`, and `user_prompt`.
2. The JWT payload supplies `tenant_id`, `user_id`, and `role`.
3. The selected `connection_ref` resolves to a decrypted target database URL.
4. Schema context is extracted from the target database.
5. LangGraph starts with a `CopilotState`.
6. Conversation memory is loaded for the thread/user/tenant.
7. Groq extracts a structured intent.
8. Clarification can pause the workflow if required fields are missing.
9. The planner resolves tables, columns, joins, filters, grouping, ordering, and limits.
10. SQL is built, normalized, and explained.
11. RBAC authorizes the requested operation.
12. `sqlglot` validation checks AST validity, schema references, DDL, dangerous functions, mutation safety, and SQL injection patterns.
13. Policy and cost/risk checks classify the workflow.
14. The workflow pauses at `waiting_for_sql_review`.
15. `/approve`, `/edit-and-approve`, or `/reject` resumes or ends the checkpointed workflow.
16. Approved SQL executes through SQLAlchemy against the tenant target database.
17. Results, errors, node traces, and metadata are saved to `workflow_runs`.

## RBAC Summary

| Role | Allowed operation intent |
| --- | --- |
| `analyst` | `SELECT` |
| `developer` | `SELECT`, `INSERT`, `UPDATE` |
| `admin` | Full configured access |

The approval routes also require `developer` or `admin` for approving SQL execution.

## Security Controls

- Passwords are hashed with bcrypt via `passlib`.
- API requests use HTTP Bearer JWT auth.
- JWT payload carries `user_id`, `tenant_id`, and `role`.
- Database URLs are encrypted at rest with Fernet.
- Tenant and user scope are checked when loading connections and checkpointed workflow state.
- SQL validation blocks DDL operations.
- `UPDATE` and `DELETE` require a `WHERE` clause.
- Suspicious SQL patterns such as comments and catalog introspection are blocked.
- Result sets are capped by `MAX_ROWS_RETURNED`.

## Tests

Run all backend tests:

```powershell
cd backend
pytest
```

Current tests cover workflow review routing, timezone-aware timestamps, JWT identity round trips, and validator safety cases.

## Docker

Build and run just the backend:

```powershell
cd backend
docker build -t ai-db-copilot-api .
docker run --env-file .env -p 8000:8000 ai-db-copilot-api
```

The container starts:

```text
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Notes for Developers

- `ensure_platform_schema()` runs during FastAPI lifespan startup and creates/verifies platform tables.
- `init_platform_db.py` can be used to initialize the platform database manually.
- `init_db.py` creates a tiny local SQLite `employees` sample database.
- `graph` is compiled in `app/core/graph/runtime.py`.
- Workflow persistence is done inside graph nodes through `save_workflow_run`.
- Keep schema and SQL changes deterministic where possible; the LLM is used for intent extraction, while planning and validation are code-driven.
