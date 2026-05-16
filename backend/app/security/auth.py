from datetime import (
    datetime,
    timedelta,
    timezone
)

from jose import jwt
from jose import JWTError

from passlib.context import (
    CryptContext
)

from fastapi import (
    HTTPException,
    status
)

from app.config import settings


# -------------------------------------------------
# PASSWORD HASHING
# -------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(
    password: str
) -> str:

    return pwd_context.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# -------------------------------------------------
# JWT TOKEN CREATION
# -------------------------------------------------

def create_access_token(
    data: dict,
    expires_minutes: int = 60
) -> str:

    to_encode = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=expires_minutes
    )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


# -------------------------------------------------
# JWT TOKEN VALIDATION
# -------------------------------------------------

def verify_access_token(
    token: str
) -> dict:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )