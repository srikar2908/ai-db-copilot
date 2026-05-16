from app.core.graph.state import (
    CopilotState
)

from app.core.graph.status import (
    WorkflowStatus
)


# -------------------------------------------------
# AFTER CLARIFICATION
# -------------------------------------------------

def route_after_clarification(
    state: CopilotState
) -> str:

    # -----------------------------------------
    # RESUME FLOW
    # -----------------------------------------

    if state.is_resumed:

        return "validate_sql"

    # -----------------------------------------
    # WAITING FOR USER
    # -----------------------------------------

    if (
        state.workflow_status
        ==
        WorkflowStatus.WAITING_FOR_CLARIFICATION
    ):

        return "end"

    # -----------------------------------------
    # NORMAL FLOW
    # -----------------------------------------

    return "generate_query_plan"


# -------------------------------------------------
# AFTER VALIDATION
# -------------------------------------------------

def route_after_validation(
    state: CopilotState
) -> str:

    validation = state.validation_result

    if (
        validation
        and
        validation.passed
    ):

        return "classify_risk"

    return "end"


# -------------------------------------------------
# AFTER RISK CLASSIFICATION
# -------------------------------------------------

def route_after_risk(state):

    # -----------------------------------------
    # BLOCKED
    # -----------------------------------------

    if state.risk_level == "blocked":

        return "end"

    # -----------------------------------------
    # ALL QUERIES GO TO SQL REVIEW
    # -----------------------------------------

    return "request_sql_review"



def route_after_sql_review(state):

    # -----------------------------------------
    # STILL WAITING
    # -----------------------------------------

    if (

        state.workflow_status

        ==

        WorkflowStatus.WAITING_FOR_SQL_REVIEW
    ):

        return "end"

    # -----------------------------------------
    # REJECTED
    # -----------------------------------------

    if (

        state.workflow_status

        ==

        WorkflowStatus.REJECTED
    ):

        return "end"

    # -----------------------------------------
    # APPROVED
    # -----------------------------------------

    if (

        state.approval

        and

        state.approval.approved
    ):

        return "execute_query"

    return "end"




# -------------------------------------------------
# AFTER APPROVAL
# -------------------------------------------------

def route_after_approval(
    state: CopilotState
) -> str:

    approval = state.approval

    if (
        approval
        and
        approval.approved is True
    ):

        return "execute_query"

    return "end"


