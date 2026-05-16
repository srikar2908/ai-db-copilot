import time

from sqlalchemy.ext.asyncio import (
    create_async_engine
)

from sqlalchemy import text

from app.models.state import (
    ExecutionResult
)


# -------------------------------------------------
# EXECUTE SQL
# -------------------------------------------------

async def execute_sql_query(

    database_url: str,

    sql: str
) -> ExecutionResult:

    # -------------------------------------------------
    # ENGINE
    # -------------------------------------------------

    engine = create_async_engine(

        database_url,

        connect_args={

            "statement_cache_size": 0
        },

        pool_pre_ping=True
    )

    start_time = time.time()

    try:

        async with engine.begin() as conn:

            result = await conn.execute(
                text(sql)
            )

            execution_time_ms = (

                time.time()
                - start_time

            ) * 1000

            # -------------------------------------------------
            # SELECT QUERIES
            # -------------------------------------------------

            if result.returns_rows:

                rows = result.fetchall()

                data = [

                    dict(row._mapping)

                    for row in rows
                ]

                return ExecutionResult(

                    success=True,

                    rows_returned=len(data),

                    rows_affected=0,

                    data=data,

                    execution_time_ms=(
                        execution_time_ms
                    ),

                    error=None
                )

            # -------------------------------------------------
            # UPDATE / INSERT / DELETE
            # -------------------------------------------------

            return ExecutionResult(

                success=True,

                rows_returned=0,

                rows_affected=result.rowcount,

                data=None,

                execution_time_ms=(
                    execution_time_ms
                ),

                error=None
            )

    except Exception as e:

        return ExecutionResult(

            success=False,

            rows_returned=0,

            rows_affected=0,

            data=None,

            execution_time_ms=0,

            error=str(e)
        )

    finally:

        await engine.dispose()