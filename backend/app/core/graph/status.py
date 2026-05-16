from enum import Enum


class WorkflowStatus(str, Enum):

    RUNNING = "running"

    WAITING_FOR_CLARIFICATION = (
        "waiting_for_clarification"
    )

    # NEW
    WAITING_FOR_SQL_REVIEW = (
        "waiting_for_sql_review"
    )

    APPROVED = "approved"

    REJECTED = "rejected"

    COMPLETED = "completed"

    FAILED = "failed"