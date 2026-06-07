# AI DB Copilot Production Audit

## 1. Executive Summary

This is a code-level audit of the checked-in backend, frontend, Docker, and database initialization code. No production traces, Supabase query plans, Render metrics, or live database credentials were available, so measured production latency and live `EXPLAIN ANALYZE` results remain required before final capacity decisions.

Overall Health Score: **6.2/10**  
Performance Score: **6.5/10**  
Security Score: **5.5/10**  
Architecture Score: **6.5/10**  
Production Readiness Score: **5.5/10**

The highest-impact completed fixes are tenant-scoped workflow/memory/connection access, actual conversation message history, async Groq and password work, schema caching, UTC-aware timestamps, result row bounds, route code splitting, indexes/migration, health check, and server-side RBAC enforcement.

## 2. Critical Issues

1. **LangGraph checkpoints are process-local.**  
   File: `backend/app/core/graph/checkpointer.py:5`  
   `MemorySaver` loses all checkpoints on Render restart/deploy and cannot coordinate multiple workers. A singleton graph now prevents multiple independent graphs inside one process, and Render is configured for one worker. Production still requires `AsyncPostgresSaver` with a dedicated checkpoint schema before scaling beyond one worker.

2. **Cross-tenant and cross-user workflow access existed.**  
   Files: `backend/app/api/history.py`, `backend/app/api/resume.py`, `backend/app/api/routes/approval.py`, `backend/app/platform/repository.py`  
   `/threads`, `/thread/{id}`, resume, and approval previously omitted authentication or ownership validation. Fixed with JWT dependency and tenant/user checks.

3. **Conversation memory was never written.**  
   File: `backend/app/core/graph/nodes.py:327`  
   `save_conversation_memory` was imported but never called. Fixed by persisting normalized plan context after plan generation.

4. **There was no message history model.**  
   Files: `backend/app/platform/models.py:302`, `backend/app/platform/messages.py`  
   The old `conversation_memory` row was only a mutable snapshot. Added append-only `conversation_messages` and a tenant/user-scoped read endpoint.

5. **Frontend-only RBAC could be bypassed.**  
   Files: `backend/app/api/connections.py`, `backend/app/api/routes/approval.py`  
   Connection creation and SQL approval are now enforced server-side.

## 3. Performance Bottlenecks

| File / Function | Problem | Impact | Applied Fix |
|---|---|---:|---|
| `backend/app/core/intent.py:371`, `extract_intent` | Synchronous Groq client inside async workflow blocked the event loop | Critical under concurrency | Switched to `AsyncGroq` and awaited completion |
| `backend/app/platform/users.py`, login/register | Bcrypt ran on the event loop | High login latency/concurrency collapse | Moved hashing/verification to AnyIO worker threads |
| `backend/app/core/schema/registry.py:20`, `extract_schema_context` | Full schema introspection and a new engine on every schema/query request | High | Added keyed 5-minute schema cache with stampede lock |
| `backend/app/core/graph/nodes.py` | Workflow persisted after most nodes, causing 6-8 platform DB writes per request | High | Not fully removed because it is audit state; phase 2 should persist only terminal/wait states |
| `backend/app/core/graph/nodes.py:770` and `:1092` | Connection lookup/decrypt and external DB engine creation repeated for cost/execution | High | Ownership lookup fixed; phase 2 needs a bounded engine registry |
| `backend/app/core/sql/executor.py` | `fetchall()` serialized unbounded result sets | High memory/latency risk | Bounded fetch to `MAX_ROWS_RETURNED` |
| `frontend/src/App.tsx` | All pages loaded in initial bundle | Medium | Added lazy route chunks |
| `frontend/src/pages/QueryHistory.tsx:103` | Filtering repeated on every render | Medium | Memoized filtered history |
| `frontend/src/components/table/DataTable.tsx:17` | Columns recalculated and component rerendered unnecessarily | Medium | Memoized columns and component |

Expected warm-path reduction from schema caching is commonly **hundreds of milliseconds to several seconds**, depending on schema size and Supabase network latency. Async Groq/bcrypt changes primarily improve concurrent throughput and tail latency. Exact reductions require Render APM traces.

## 4. Conversation Memory Issues

Root causes:

- `save_conversation_memory` had zero call sites.
- Reads and updates filtered only by user-controlled `thread_id`.
- `thread_id` was globally unique, causing collisions between tenants/users.
- The table represented one context snapshot, not a conversation.
- LangGraph checkpoints were volatile and split across graph instances.

Fixes:

- Tenant/user filters added to memory read/write.
- Composite unique scope added: `(tenant_id, user_id, thread_id)`.
- Plan context now persists after successful plan generation.
- Append-only `conversation_messages` table and endpoint added.
- A single graph runtime instance is used in-process.

Remaining: replace `MemorySaver` with Postgres checkpoint persistence.

## 5. Timestamp Issues

Root cause: SQLAlchemy used naive `DateTime`, backend used `datetime.utcnow()`, and connection dates used browser-local formatting.

Production standard: **store UTC in `timestamptz`; convert to Asia/Kolkata only in the display layer.**

Applied:

- `utc_now()` returns timezone-aware UTC.
- SQLAlchemy timestamp columns use `DateTime(timezone=True)`.
- Migration converts existing columns using `AT TIME ZONE 'UTC'`.
- Frontend uses a shared `Asia/Kolkata` formatter.

Migration: `backend/migrations/001_production_hardening.sql`.

## 6. Database Improvements

Added indexes:

- `workflow_runs (tenant_id, created_at DESC)`
- `workflow_runs (tenant_id, user_id, thread_id)`
- `database_connections (tenant_id, owner_user_id)`
- unique `database_connections (tenant_id, connection_ref)`
- `conversation_memory (tenant_id, user_id, thread_id, updated_at DESC)`
- `conversation_messages (tenant_id, user_id, thread_id, created_at ASC)`

Recommended follow-up:

- Change `workflow_runs` from a mutable thread row into append-only workflow turns.
- Add foreign keys after tenant/user identifier types are normalized.
- Enable Supabase RLS as defense in depth.
- Capture `EXPLAIN (ANALYZE, BUFFERS)` for platform history and memory queries.

## 7. Security Findings

Critical:

- Volatile LangGraph checkpointing can resume incorrectly after restarts; persistent checkpointer required.

High:

- Public registration accepts caller-selected tenant IDs. Introduce invite/provisioning tokens before public production use.
- JWTs have no issuer, audience, token ID, refresh/revocation, or key rotation.
- No API rate limiting or abuse controls.
- External database credentials grant whatever rights the configured DB user has. Use read-only credentials by default and separate mutation credentials.
- SQL and workflow state are printed to stdout in several nodes; remove or redact before production.

Medium:

- Static CORS list should be environment-driven.
- No statement timeout/cancellation for external queries.
- Prompt injection is not explicitly isolated from schema/tool instructions.
- Errors can expose external database details to clients.
- No Supabase RLS policies are included in the repository.

Low:

- Duplicate/dead modules and verbose comments increase maintenance cost.
- Dependency list is much larger than the imported runtime surface.

## 8. Testing Report

Coverage: no existing project test suite or frontend test runner was present.

Generated:

- `backend/tests/test_production_guards.py`
- `backend/tests/test_routing.py`
- `backend/tests/conftest.py`
- `backend/pytest.ini`

Verification:

- Backend compile: passed.
- Frontend production build: passed.
- Frontend lint: passed.
- Pytest execution: blocked because the available system Python does not have `pytest`, and the checked-in virtualenv points to a missing interpreter.

Missing tests:

- Postgres/Supabase integration tests for tenant isolation and migration.
- Concurrent memory upsert tests.
- Persistent checkpoint restart/resume tests.
- External query timeout and row-limit tests.
- Frontend component/API tests.
- End-to-end login/query/approve/history tests.

## 9. Refactoring Plan

### Phase 1 (Immediate)

- Apply `backend/migrations/001_production_hardening.sql`.
- Deploy with `WEB_CONCURRENCY=1` until Postgres checkpointing is complete.
- Remove/redact SQL and workflow `print` statements.
- Add invitation-based tenant provisioning and rate limiting.

### Phase 2 (Performance)

- Replace `MemorySaver` with `AsyncPostgresSaver`.
- Add a bounded, TTL-based external database engine registry.
- Persist workflow audit records only at wait/terminal/error boundaries.
- Add request/node timing metrics and structured JSON logs.
- Add statement timeouts and cancellation.

Optimized workflow:

`load cached schema + memory -> async intent LLM -> clarification -> deterministic plan/build/validate/RBAC -> cost check -> approval checkpoint -> execute -> terminal audit + memory`

This removes repeated schema work, avoids event-loop blocking, and reduces intermediate state writes.

### Phase 3 (Production)

- Supabase RLS and tested disaster recovery.
- OpenTelemetry/APM, SLOs, alerts, and dashboards.
- Load tests for login, schema, query, approval, and history.
- Separate read-only and mutation database credentials.
- Multi-worker deployment only after persistent checkpointing.

## 10. Exact Code Patches

Implemented patches are present in the workspace. Primary artifacts:

- `backend/migrations/001_production_hardening.sql`
- `backend/app/platform/messages.py`
- `backend/app/core/graph/runtime.py`
- `backend/app/utils/time.py`
- `backend/tests/`
- `frontend/src/utils/date.ts`
- `render.yaml`

Recommended Render backend startup command:

```sh
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips='*'
```

Use one worker now because the checkpointer is process-local. After Postgres checkpointing and load testing, start with two workers on a plan with at least 1 GB RAM.
