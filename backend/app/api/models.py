from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):

    thread_id: str

    connection_ref: str

    user_prompt: str

class ApprovalRequest(
    BaseModel
):

    thread_id: str

    approval_status: str

    approved_sql: str | None = None


class ConnectionRequest(BaseModel):

    connection_ref: str

    database_type: str

    database_url: str | None = None

    host: str | None = None

    port: int | None = None

    username: str | None = None

    password: str | None = None

    database_name: str | None = None

    file_path: str | None = None

    ssl_enabled: bool = False


class RegisterRequest(BaseModel):

    tenant_id: str

    email: str

    password: str

    full_name: str

    role: Optional[str] = "analyst"


class LoginRequest(BaseModel):

    email: str

    password: str
