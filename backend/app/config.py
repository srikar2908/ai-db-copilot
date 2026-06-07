from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Database Copilot"

    GROQ_API_KEY: str
    GROQ_MODEL: str

    DATABASE_URL: str

    ENCRYPTION_KEY: str
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    MAX_QUERY_COST: int = 10000
    MAX_ROWS_RETURNED: int = 5000
    SCHEMA_CACHE_TTL_SECONDS: int = 300
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT_SECONDS: int = 10

    LLM_TEMPERATURE: float = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
