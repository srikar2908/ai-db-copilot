from sqlalchemy import (
    select,
    and_
)

from app.platform.database import (
    AsyncSessionLocal
)

from app.platform.models import (
    DatabaseConnection
)

from app.security.encryption import (
    encrypt_value,
    decrypt_value
)

from app.db.test_connection import (
    test_database_connection
)


# -------------------------------------------------
# CREATE CONNECTION
# -------------------------------------------------

async def create_connection(

    tenant_id: str,

    owner_user_id: str,

    connection_ref: str,

    database_url: str,

    database_type: str
):

    # -------------------------------------------------
    # TEST DATABASE CONNECTION
    # -------------------------------------------------

    is_valid = await test_database_connection(
        database_url
    )

    if not is_valid:

        raise ValueError(
            "Database connection failed"
        )

    # -------------------------------------------------
    # ENCRYPT DATABASE URL
    # -------------------------------------------------

    encrypted_url = encrypt_value(
        database_url
    )

    async with AsyncSessionLocal() as session:

        # -------------------------------------------------
        # CHECK EXISTING CONNECTION
        # -------------------------------------------------

        existing = await session.execute(

            select(DatabaseConnection).where(

                and_(

                    DatabaseConnection.tenant_id
                    == tenant_id,

                    DatabaseConnection.connection_ref
                    == connection_ref
                )
            )
        )

        existing_connection = (
            existing.scalar_one_or_none()
        )

        if existing_connection:

            raise ValueError(
                "Connection already exists"
            )

        # -------------------------------------------------
        # CREATE CONNECTION
        # -------------------------------------------------

        connection = DatabaseConnection(

            tenant_id=tenant_id,

            owner_user_id=owner_user_id,

            connection_ref=connection_ref,

            encrypted_database_url=encrypted_url,

            database_type=database_type
        )

        session.add(connection)

        await session.commit()

        return {

            "message":
                "Connection created",

            "connection_ref":
                connection_ref
        }




# -------------------------------------------------
# GET SINGLE CONNECTION
# -------------------------------------------------

async def get_connection(

    tenant_id: str,

    user_id: int,

    connection_ref: str
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(DatabaseConnection).where(

                DatabaseConnection.connection_ref
                == connection_ref,

                DatabaseConnection.tenant_id
                == tenant_id
            )
        )

        connection = (
            result.scalar_one_or_none()
        )

        if not connection:

            return None

        # -------------------------------------------------
        # DECRYPT DATABASE URL
        # -------------------------------------------------

        decrypted_url = decrypt_value(

            connection.encrypted_database_url
        )

        connection.database_url = (
            decrypted_url
        )

        return connection



# -------------------------------------------------
# LIST CONNECTIONS
# -------------------------------------------------

async def list_connections(

    tenant_id: str,

    owner_user_id: int
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(DatabaseConnection).where(

                DatabaseConnection.tenant_id
                == tenant_id
            )
        )

        connections = result.scalars().all()

        return [

            {
                "tenant_id":
                    conn.tenant_id,

                "connection_ref":
                    conn.connection_ref,

                "database_type":
                    conn.database_type,

                "created_at":
                    conn.created_at,

                "owner_user_id":
                    conn.owner_user_id
            }

            for conn in connections
        ]