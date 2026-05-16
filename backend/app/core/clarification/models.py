from pydantic import BaseModel


class ClarificationResult(BaseModel):

    requires_clarification: bool

    missing_fields: list[str]

    question: str | None = None