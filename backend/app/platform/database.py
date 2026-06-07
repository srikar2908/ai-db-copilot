from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from sqlalchemy.orm import declarative_base

from app.config import settings


# =========================================================
# DATABASE URL
# =========================================================

DATABASE_URL = settings.DATABASE_URL

# =========================================================
# ASYNC ENGINE
# =========================================================

engine = create_async_engine(

    DATABASE_URL,

    echo=False,

    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,

    connect_args={
        "statement_cache_size": 0,
        "server_settings": {
            "timezone": "UTC"
        }
    }
)

# =========================================================
# SESSION
# =========================================================

AsyncSessionLocal = async_sessionmaker(

    bind=engine,

    class_=AsyncSession,

    expire_on_commit=False
)

# =========================================================
# BASE
# =========================================================

Base = declarative_base()
