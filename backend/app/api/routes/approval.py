from datetime import datetime

from fastapi import APIRouter, Depends

from app.models.api import (

    ApproveRequest,

    RejectRequest,

    EditAndApproveRequest
)

from app.core.graph.builder import (
    build_graph
)

from app.core.graph.state import (
    CopilotState
)

from app.core.graph.status import (
    WorkflowStatus
)

from app.core.sql.normalizer import (
    normalize_sql
)

from app.core.sql.reviewer import (
    review_sql_edit
)

from app.core.sql.validator import (
    validate_sql_query
)
from app.security.dependencies import (
    get_current_user
)

router = APIRouter()

graph = build_graph()


# -------------------------------------------------
# LOAD WORKFLOW STATE
# -------------------------------------------------

# -------------------------------------------------
# LOAD WORKFLOW STATE
# -------------------------------------------------

async def load_workflow_state(
    thread_id: str
):

    config = {

        "configurable": {

            "thread_id": thread_id
        }
    }

    checkpoint = await graph.aget_state(
        config
    )

    # -----------------------------------------
    # NOT FOUND
    # -----------------------------------------

    if not checkpoint:

        return None, config

    # -----------------------------------------
    # DEBUG
    # -----------------------------------------

    print("\nCHECKPOINT:")
    print(checkpoint)

    # -----------------------------------------
    # LANGGRAPH VALUES
    # -----------------------------------------

    state_values = checkpoint.values

    if not state_values:

        return None, config

    # -----------------------------------------
    # REBUILD STATE
    # -----------------------------------------

    workflow_state = CopilotState(
        **state_values
    )

    return workflow_state, config


# -------------------------------------------------
# APPROVE EXISTING SQL
# -------------------------------------------------

@router.post("/approve")
async def approve_sql(

    request: ApproveRequest,

    current_user=Depends(
        get_current_user
    )
):

    workflow_state, config = (
        await load_workflow_state(
            request.thread_id
        )
    )

    if not workflow_state:

        return {
            "error":
                "Workflow not found"
        }

    # -----------------------------------------
    # VALIDATE STATUS
    # -----------------------------------------

    allowed_review_statuses = [
        WorkflowStatus.WAITING_FOR_SQL_REVIEW,
        WorkflowStatus.FAILED
    ]

    if workflow_state.workflow_status not in allowed_review_statuses:

        return {

            "error":

                "Workflow is not waiting "
                "for SQL review"
        }

    if request.approval_status != "approved":

        workflow_state.approval.required = False

        workflow_state.approval.approved = False

        workflow_state.approval.reason = (
            "Rejected by user"
        )

        workflow_state.workflow_status = (
            WorkflowStatus.REJECTED
        )

        workflow_state.updated_at = (
            datetime.utcnow()
        )

        workflow_state.node_trace.append(
            "sql_rejected"
        )

        return {

            "thread_id":
                request.thread_id,

            "approval_status":
                "rejected"
        }

    if request.approved_sql:

        edited_request = EditAndApproveRequest(
            thread_id=request.thread_id,
            edited_sql=request.approved_sql
        )

        return await edit_and_approve(
            edited_request,
            current_user
        )

    # -----------------------------------------
    # APPROVE EXISTING SQL
    # -----------------------------------------

    workflow_state.approval.required = False

    workflow_state.approval.approved = True

    workflow_state.approval.reason = (
        "Approved by user"
    )

    workflow_state.workflow_status = (
        WorkflowStatus.APPROVED
    )

    workflow_state.approval_timestamp = (
        datetime.utcnow()
    )

    workflow_state.is_resumed = True

    workflow_state.node_trace.append(
        "sql_approved"
    )

    # -----------------------------------------
    # RESUME GRAPH
    # -----------------------------------------

    result = await graph.ainvoke(

        workflow_state.model_dump(),

        config=config
    )

    return result


# -------------------------------------------------
# EDIT SQL + APPROVE
# -------------------------------------------------

# -------------------------------------------------
# EDIT SQL + APPROVE
# -------------------------------------------------

# -------------------------------------------------
# EDIT SQL + APPROVE
# -------------------------------------------------

@router.post("/edit-and-approve")
async def edit_and_approve(

    request: EditAndApproveRequest,

    current_user=Depends(
        get_current_user
    )
):

    workflow_state, config = (
        await load_workflow_state(
            request.thread_id
        )
    )

    # -----------------------------------------
    # WORKFLOW EXISTS
    # -----------------------------------------

    if not workflow_state:

        return {

            "error":
                "Workflow not found"
        }

    # -----------------------------------------
    # VALIDATE STATUS
    # -----------------------------------------

    allowed_review_statuses = [
        WorkflowStatus.WAITING_FOR_SQL_REVIEW,
        WorkflowStatus.FAILED
    ]

    if workflow_state.workflow_status not in allowed_review_statuses:

        return {

            "error":

                "Workflow is not waiting "
                "for SQL review"
        }

    # -----------------------------------------
    # ORIGINAL SQL
    # -----------------------------------------

    original_sql = (
        workflow_state.generated_sql
    )

    # -----------------------------------------
    # NORMALIZE SQL
    # -----------------------------------------

    normalized_sql = normalize_sql(
        request.edited_sql
    )

    # -----------------------------------------
    # VALIDATE SQL
    # -----------------------------------------

    validation_result = (
        validate_sql_query(
            normalized_sql,
            schema_context=workflow_state.schema_context
        )
    )

    if not validation_result.passed:

        return {

            "error":
                "SQL validation failed",

            "validation_errors":
                validation_result.errors,

            "warnings":
                validation_result.warnings
        }

    # -----------------------------------------
    # REVIEW EDITS
    # -----------------------------------------

    review_result = review_sql_edit(

        original_sql=original_sql,

        edited_sql=normalized_sql
    )

    # -----------------------------------------
    # BLOCK UNSAFE SQL
    # -----------------------------------------

    if not review_result["safe_to_execute"]:

        return {

            "error":
                "Edited SQL blocked",

            "review_result":
                review_result
        }

    # -----------------------------------------
    # STORE SQLS
    # -----------------------------------------

    workflow_state.original_generated_sql = (
        original_sql
    )

    workflow_state.generated_sql = (
        normalized_sql
    )

    workflow_state.approved_sql = (
        normalized_sql
    )

    workflow_state.errors = []

    workflow_state.execution_result = None

    # -----------------------------------------
    # STORE REVIEW
    # -----------------------------------------

    workflow_state.review_result = (
        review_result
    )

    # -----------------------------------------
    # UPDATE RISK
    # -----------------------------------------

    workflow_state.risk_level = (
        review_result["edited_risk"]
    )

    # -----------------------------------------
    # APPROVAL STATE
    # -----------------------------------------

    workflow_state.approval.required = False

    workflow_state.approval.approved = True

    workflow_state.approval.reason = (
        "Edited and approved by user"
    )

    workflow_state.workflow_status = (
        WorkflowStatus.APPROVED
    )

    workflow_state.approval_timestamp = (
        datetime.utcnow()
    )

    workflow_state.updated_at = (
        datetime.utcnow()
    )

    workflow_state.is_resumed = True

    # -----------------------------------------
    # TRACE
    # -----------------------------------------

    workflow_state.node_trace.append(
        "manual_sql_edit"
    )

    workflow_state.node_trace.append(
        "sql_review_completed"
    )

    workflow_state.node_trace.append(
        "sql_edited_and_approved"
    )

    # -----------------------------------------
    # RESUME GRAPH
    # -----------------------------------------

    result = await graph.ainvoke(

        workflow_state.model_dump(),

        config=config
    )

    return result
# -------------------------------------------------
# REJECT SQL
# -------------------------------------------------

@router.post("/reject")
async def reject_sql(

    request: RejectRequest
):

    workflow_state, config = (
        await load_workflow_state(
            request.thread_id
        )
    )

    if not workflow_state:

        return {
            "error":
                "Workflow not found"
        }

    workflow_state.approval.required = False

    workflow_state.approval.approved = False

    workflow_state.approval.reason = (
        request.reason
        or
        "Rejected by user"
    )

    workflow_state.workflow_status = (
        WorkflowStatus.REJECTED
    )

    workflow_state.updated_at = (
        datetime.utcnow()
    )

    workflow_state.node_trace.append(
        "sql_rejected"
    )

    return {

        "thread_id":
            request.thread_id,

        "status":
            "rejected"
    }
