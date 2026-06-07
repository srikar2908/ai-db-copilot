import hashlib
import asyncio
import time

from sqlalchemy import inspect

from sqlalchemy.ext.asyncio import (
    create_async_engine
)

from app.models.state import SchemaContext
from app.config import settings
from app.utils.time import utc_now


_schema_cache: dict[str, tuple[float, SchemaContext]] = {}
_schema_locks: dict[str, asyncio.Lock] = {}


async def extract_schema_context(
    database_url: str
) -> SchemaContext:
    cache_key = hashlib.sha256(database_url.encode()).hexdigest()
    cached = _schema_cache.get(cache_key)

    if cached and cached[0] > time.monotonic():
        return cached[1]

    lock = _schema_locks.setdefault(cache_key, asyncio.Lock())

    async with lock:
        cached = _schema_cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]

        engine = create_async_engine(
            database_url,
            connect_args={"statement_cache_size": 0},
            pool_pre_ping=True,
        )

        try:
            async with engine.connect() as conn:

                def get_schema(sync_conn):

                    inspector = inspect(sync_conn)

                    tables = inspector.get_table_names()

                    schema_data = {}

                    for table in tables:

                        columns = inspector.get_columns(table)

                        schema_data[table] = [
                            column["name"]
                            for column in columns
                        ]

                    return schema_data

                schema_data = await conn.run_sync(get_schema)
        finally:
            await engine.dispose()

        schema_string = str(schema_data)

        schema_hash = hashlib.sha256(
            schema_string.encode()
        ).hexdigest()

        schema = SchemaContext(
            tables=schema_data,
            relevant_tables=list(schema_data.keys()),
            schema_version=schema_hash,
            extracted_at=utc_now()
        )
        _schema_cache[cache_key] = (
            time.monotonic() + settings.SCHEMA_CACHE_TTL_SECONDS,
            schema,
        )
        return schema
