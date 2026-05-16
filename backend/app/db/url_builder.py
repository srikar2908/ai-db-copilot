def build_database_url(

    database_type: str,

    host: str | None = None,

    port: int | None = None,

    username: str | None = None,

    password: str | None = None,

    database_name: str | None = None,

    file_path: str | None = None,

    ssl_enabled: bool = False
) -> str:

    # -------------------------------------------------
    # SQLITE
    # -------------------------------------------------

    if database_type == "sqlite":

        if not file_path:

            raise ValueError(
                "SQLite requires file_path"
            )

        return (
            f"sqlite+aiosqlite:///"
            f"{file_path}"
        )

    # -------------------------------------------------
    # POSTGRESQL
    # -------------------------------------------------

    elif database_type == "postgresql":

        if not all([
            host,
            port,
            username,
            password,
            database_name
        ]):
            raise ValueError(
                "Missing PostgreSQL fields"
            )

        ssl_part = ""

        if ssl_enabled:

            ssl_part = "?ssl=require"

        return (
            f"postgresql+asyncpg://"
            f"{username}:{password}"
            f"@{host}:{port}"
            f"/{database_name}"
            f"{ssl_part}"
        )

    # -------------------------------------------------
    # MYSQL
    # -------------------------------------------------

    elif database_type == "mysql":

        if not all([
            host,
            port,
            username,
            password,
            database_name
        ]):
            raise ValueError(
                "Missing MySQL fields"
            )

        return (
            f"mysql+aiomysql://"
            f"{username}:{password}"
            f"@{host}:{port}"
            f"/{database_name}"
        )

    # -------------------------------------------------
    # UNSUPPORTED
    # -------------------------------------------------

    else:

        raise ValueError(
            f"Unsupported database type: "
            f"{database_type}"
        )