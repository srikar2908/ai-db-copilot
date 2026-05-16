from sqlalchemy import select

from app.platform.database import (
    AsyncSessionLocal
)

from app.platform.models import (
    PlatformUser
)

from app.security.auth import (
    hash_password,
    verify_password,
    create_access_token
)


# -------------------------------------------------
# ALLOWED ROLES
# -------------------------------------------------

ALLOWED_ROLES = {
    "admin",
    "developer",
    "analyst"
}


# -------------------------------------------------
# REGISTER USER
# -------------------------------------------------

async def register_user(

    tenant_id: str,

    email: str,

    password: str,

    full_name: str,

    role: str = "analyst"
):

    async with AsyncSessionLocal() as session:

        # -----------------------------------------
        # CHECK EXISTING USER
        # -----------------------------------------

        existing = await session.execute(

            select(PlatformUser).where(

                PlatformUser.email == email
            )
        )

        user = existing.scalar_one_or_none()

        if user:

            raise ValueError(
                "User already exists"
            )

        # -----------------------------------------
        # VALIDATE ROLE
        # -----------------------------------------

        role = role.lower().strip()

        if role not in ALLOWED_ROLES:

            raise ValueError(
                f"Invalid role: {role}"
            )

        # -----------------------------------------
        # HASH PASSWORD
        # -----------------------------------------

        hashed = hash_password(
            password
        )

        # -----------------------------------------
        # CREATE USER
        # -----------------------------------------

        new_user = PlatformUser(

            tenant_id=tenant_id,

            email=email,

            hashed_password=hashed,

            full_name=full_name,

            role=role
        )

        session.add(new_user)

        await session.commit()

        return {

            "message":
                "User registered",

            "role":
                role
        }


# -------------------------------------------------
# LOGIN USER
# -------------------------------------------------

async def login_user(

    email: str,

    password: str
):

    async with AsyncSessionLocal() as session:

        # -----------------------------------------
        # FIND USER
        # -----------------------------------------

        result = await session.execute(

            select(PlatformUser).where(

                PlatformUser.email == email
            )
        )

        user = result.scalar_one_or_none()

        if not user:

            raise ValueError(
                "Invalid credentials"
            )

        # -----------------------------------------
        # VERIFY PASSWORD
        # -----------------------------------------

        valid = verify_password(

            password,

            user.hashed_password
        )

        if not valid:

            raise ValueError(
                "Invalid credentials"
            )

        # -----------------------------------------
        # CREATE TOKEN
        # -----------------------------------------

        token = create_access_token(
            {
                "user_id": user.id,

                "tenant_id": user.tenant_id,

                "email": user.email,

                "role": user.role
            }
        )

        # -----------------------------------------
        # RETURN
        # -----------------------------------------

        return {

            "access_token": token,

            "token_type": "bearer",

            "user": {

                "id": user.id,

                "email": user.email,

                "tenant_id": user.tenant_id,

                "full_name": user.full_name,

                "role": user.role
            }
        }