from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from app.api.models import (
    ConnectionRequest
)

from app.platform.connections import (
    create_connection,
    list_connections
)

from app.db.url_builder import (
    build_database_url
)

from app.security.dependencies import (
    get_current_user
)

router = APIRouter()


# -------------------------------------------------
# CREATE CONNECTION
# -------------------------------------------------

@router.post("/connections")
async def add_connection(

    request: ConnectionRequest,

    current_user=Depends(
        get_current_user
    )
):

    try:

        # -------------------------------------------------
        # AUTHENTICATED TENANT
        # -------------------------------------------------

        tenant_id = current_user[
            "tenant_id"
        ]

        # -------------------------------------------------
        # BUILD DATABASE URL
        # -------------------------------------------------

        database_url = (
            request.database_url
            or
            build_database_url(

                database_type=request.database_type,

                host=request.host,

                port=request.port,

                username=request.username,

                password=request.password,

                database_name=request.database_name,

                file_path=request.file_path,

                ssl_enabled=request.ssl_enabled
            )
        )

        # -------------------------------------------------
        # CREATE CONNECTION
        # -------------------------------------------------

        return await create_connection(

            tenant_id=tenant_id,

            owner_user_id=current_user["user_id"],

            connection_ref=request.connection_ref,

            database_url=database_url,

            database_type=request.database_type
        )

    except ValueError as e:

        raise HTTPException(

            status_code=400,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Internal server error: {str(e)}"
        )


# -------------------------------------------------
# LIST CONNECTIONS
# -------------------------------------------------

# -------------------------------------------------
# LIST CONNECTIONS
# -------------------------------------------------

@router.get("/connections")
async def get_connections(

    current_user=Depends(
        get_current_user
    )
):

    try:

        return await list_connections(

            tenant_id=current_user["tenant_id"],

            owner_user_id=current_user["user_id"]
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Failed to fetch connections: {str(e)}"
        )
