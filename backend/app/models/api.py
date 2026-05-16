from pydantic import BaseModel


class QueryRequest(BaseModel):

    prompt: str


from pydantic import BaseModel


class ApproveRequest(BaseModel):

    thread_id: str


class RejectRequest(BaseModel):

    thread_id: str

    reason: str | None = None


class EditAndApproveRequest(BaseModel):

    thread_id: str

    edited_sql: str