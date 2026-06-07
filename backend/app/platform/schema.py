import logging

from sqlalchemy import text

from app.platform.database import Base, engine
from app.platform import models  # noqa: F401


logger = logging.getLogger(__name__)

TIMESTAMP_COLUMNS = {
    "workflow_runs": ("created_at", "updated_at", "approval_timestamp"),
    "database_connections": ("created_at",),
    "platform_users": ("created_at",),
    "conversation_memory": ("created_at", "updated_at"),
    "conversation_messages": ("created_at",),
}

INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS ix_workflow_runs_tenant_created "
    "ON workflow_runs (tenant_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_workflow_runs_tenant_user_thread "
    "ON workflow_runs (tenant_id, user_id, thread_id)",
    "CREATE INDEX IF NOT EXISTS ix_database_connections_tenant_owner "
    "ON database_connections (tenant_id, owner_user_id)",
    "CREATE INDEX IF NOT EXISTS ix_conversation_memory_scope_updated "
    "ON conversation_memory (tenant_id, user_id, thread_id, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_conversation_messages_scope_created "
    "ON conversation_messages (tenant_id, user_id, thread_id, created_at ASC)",
)


async def ensure_platform_schema() -> None:
    """Apply safe, idempotent schema corrections needed by the running app."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

        if connection.dialect.name == "postgresql":
            for table, columns in TIMESTAMP_COLUMNS.items():
                for column in columns:
                    result = await connection.execute(
                        text(
                            """
                            SELECT data_type
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = :table
                              AND column_name = :column
                            """
                        ),
                        {"table": table, "column": column},
                    )

                    if result.scalar_one_or_none() == "timestamp without time zone":
                        await connection.execute(
                            text(
                                f'ALTER TABLE "{table}" '
                                f'ALTER COLUMN "{column}" TYPE timestamptz '
                                f'USING "{column}" AT TIME ZONE \'UTC\''
                            )
                        )

            for statement in INDEX_STATEMENTS:
                await connection.execute(text(statement))

    logger.info("Platform database schema verified")
