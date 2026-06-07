from app.core.graph.routing import route_after_sql_review
from app.core.graph.state import CopilotState
from app.core.graph.status import WorkflowStatus
from app.models.state import ApprovalState
from app.utils.time import utc_now


def state(**overrides) -> CopilotState:
    values = {
        "session_id": "thread-1",
        "tenant_id": "tenant-a",
        "user_id": "1",
        "user_role": "analyst",
        "connection_ref": "connection-1",
        "user_prompt": "show employees",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    values.update(overrides)
    return CopilotState(**values)


def test_review_waits_for_explicit_approval():
    workflow = state(
        workflow_status=WorkflowStatus.WAITING_FOR_SQL_REVIEW,
        approval=ApprovalState(required=True, approved=False),
    )

    assert route_after_sql_review(workflow) == "end"


def test_approved_review_routes_to_execution():
    workflow = state(
        workflow_status=WorkflowStatus.APPROVED,
        approval=ApprovalState(required=False, approved=True),
    )

    assert route_after_sql_review(workflow) == "execute_query"
