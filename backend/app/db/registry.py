from app.platform.connections import (
    get_connection
)


async def get_database_url(

    tenant_id: str,

    user_id: int,

    connection_ref: str
) -> str:

    connection = await get_connection(

        tenant_id=tenant_id,

        user_id=user_id,

        connection_ref=connection_ref
    )

    if not connection:

        raise ValueError(

            f"Unknown connection_ref: "
            f"{connection_ref}"
        )

    return connection.database_url