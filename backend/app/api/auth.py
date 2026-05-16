from fastapi import (
    APIRouter,
    HTTPException
)

from app.api.models import (
    RegisterRequest,
    LoginRequest
)

from app.platform.users import (
    register_user,
    login_user
)

router = APIRouter()


# -------------------------------------------------
# REGISTER
# -------------------------------------------------

@router.post("/register")
async def register_endpoint(
    request: RegisterRequest
):

    try:

        return await register_user(

            tenant_id=request.tenant_id,

            email=request.email,

            password=request.password,

            full_name=request.full_name,

            role=request.role
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

@router.post("/login")
async def login_endpoint(
    request: LoginRequest
):

    try:

        return await login_user(

            email=request.email,

            password=request.password
        )

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )