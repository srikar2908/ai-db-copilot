BEGIN;

SET TIME ZONE 'UTC';

ALTER TABLE workflow_runs
    ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC',
    ALTER COLUMN approval_timestamp TYPE timestamptz USING approval_timestamp AT TIME ZONE 'UTC';

ALTER TABLE database_connections
    ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';

ALTER TABLE platform_users
    ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';

ALTER TABLE conversation_memory
    ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE workflow_runs
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN updated_at SET DEFAULT now();

ALTER TABLE database_connections
    ALTER COLUMN created_at SET DEFAULT now();

ALTER TABLE platform_users
    ALTER COLUMN created_at SET DEFAULT now();

ALTER TABLE conversation_memory
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN updated_at SET DEFAULT now();

ALTER TABLE conversation_memory DROP CONSTRAINT IF EXISTS conversation_memory_thread_id_key;
ALTER TABLE conversation_memory
    ADD CONSTRAINT uq_conversation_memory_scope UNIQUE (tenant_id, user_id, thread_id);

CREATE INDEX IF NOT EXISTS ix_workflow_runs_tenant_created
    ON workflow_runs (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_workflow_runs_tenant_user_thread
    ON workflow_runs (tenant_id, user_id, thread_id);
CREATE INDEX IF NOT EXISTS ix_database_connections_tenant_owner
    ON database_connections (tenant_id, owner_user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_database_connections_tenant_ref
    ON database_connections (tenant_id, connection_ref);
CREATE INDEX IF NOT EXISTS ix_conversation_memory_scope_updated
    ON conversation_memory (tenant_id, user_id, thread_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id text PRIMARY KEY,
    thread_id text NOT NULL,
    tenant_id text NOT NULL,
    user_id text NOT NULL,
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_conversation_messages_scope_created
    ON conversation_messages (tenant_id, user_id, thread_id, created_at ASC);

COMMIT;
