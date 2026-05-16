from pydantic import BaseModel

from typing import List


class PolicyResult(BaseModel):

    allowed: bool

    risk_level: str

    errors: List[str]

    warnings: List[str]