from sqlalchemy.ext.asyncio import (
    create_async_engine
)

from sqlalchemy import text


async def test_database_connection(
    database_url: str
) -> bool:

    engine = create_async_engine(

        database_url,
        connect_args={
        "statement_cache_size": 0
    },

        pool_pre_ping=True
    )

    try:

        async with engine.connect() as conn:

            await conn.execute(
                text("SELECT 1")
            )

        return True

    except Exception as e:

        print(
            "Database connection failed:",
            str(e)
        )

        return False

    finally:

        await engine.dispose()