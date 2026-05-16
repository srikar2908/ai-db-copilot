from pydantic import BaseModel

from typing import List


class QueryCostAnalysis(BaseModel):

    success: bool

    estimated_cost: float | None

    estimated_rows: int | None

    risk_level: str

    warnings: List[str]

    raw_plan: str | None