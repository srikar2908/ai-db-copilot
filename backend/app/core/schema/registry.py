import hashlib

from datetime import datetime

from sqlalchemy import inspect

from sqlalchemy.ext.asyncio import (
    create_async_engine
)

from app.models.state import SchemaContext


async def extract_schema_context(
    database_url: str
) -> SchemaContext:

    #engine = create_async_engine(database_url)

    engine = create_async_engine(
    database_url,
    connect_args={
        "statement_cache_size": 0
    }
)

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

        schema_data = await conn.run_sync(
            get_schema
        )

    schema_string = str(schema_data)

    schema_hash = hashlib.md5(
        schema_string.encode()
    ).hexdigest()

    return SchemaContext(
        tables=schema_data,
        relevant_tables=list(schema_data.keys()),
        schema_version=schema_hash,
        extracted_at=datetime.utcnow()
    )