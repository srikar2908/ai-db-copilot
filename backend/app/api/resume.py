from fastapi import APIRouter, Depends

from app.core.graph.runtime import (
    graph
)

from app.core.graph.state import (
    CopilotState
)

from app.core.graph.status import (
    WorkflowStatus
)

from app.core.clarification.resolver import (
    resolve_clarification
)
from app.security.dependencies import get_current_user


router = APIRouter()

@router.post("/workflow/resume")
async def resume_workflow(

    session_id: str,

    clarification_response: str,
    current_user=Depends(get_current_user)
):

    # -------------------------------------------------
    # GRAPH CONFIG
    # -------------------------------------------------

    config = {

        "configurable": {

            "thread_id": session_id
        }
    }

    # -------------------------------------------------
    # LOAD CHECKPOINT
    # -------------------------------------------------

    checkpoint_state = await graph.aget_state(
        config
    )

    if not checkpoint_state:

        return {

            "error":
                "Workflow state not found."
        }

    # -------------------------------------------------
    # REBUILD STATE OBJECT
    # -------------------------------------------------

    workflow_state = CopilotState(
        **checkpoint_state.values
    )

    if (
        workflow_state.tenant_id != current_user["tenant_id"]
        or workflow_state.user_id != str(current_user["user_id"])
    ):
        return {"error": "Workflow not found."}

    # -------------------------------------------------
    # VALIDATE STATUS
    # -------------------------------------------------

    if (

        workflow_state.workflow_status

        !=

        WorkflowStatus.WAITING_FOR_CLARIFICATION
    ):

        return {

            "error":
                "Workflow is not waiting "
                "for clarification."
        }

    # -------------------------------------------------
    # UPDATE CLARIFICATION STATE
    # -------------------------------------------------

    workflow_state.clarification.user_response = (
        clarification_response
    )

    workflow_state.clarification.required = False

    workflow_state.workflow_status = (
        WorkflowStatus.RUNNING
    )

    workflow_state.is_resumed = True

    workflow_state.node_trace.append(
        "workflow_resumed"
    )

    # -------------------------------------------------
    # RESOLVE CLARIFICATION
    # -------------------------------------------------

    intent = workflow_state.extracted_intent

    schema_context = (
        workflow_state.schema_context
    )

    clarification_fields = (
        workflow_state
        .clarification
        .missing_fields
    )

    if intent and schema_context:

        resolved_intent = (
            resolve_clarification(

                intent=intent,

                schema_context=schema_context,

                clarification_fields=
                    clarification_fields,

                clarification_response=
                    clarification_response
            )
        )

        # ---------------------------------------------
        # REBUILD NESTED STATE
        # ---------------------------------------------

        workflow_state.extracted_intent = (
            resolved_intent
        )

        print(

            "RESOLVED INTENT:",

            resolved_intent.model_dump()
        )

    # -------------------------------------------------
    # CLEAR CLARIFICATION FLAGS
    # -------------------------------------------------

    workflow_state.clarification.missing_fields = []

    workflow_state.clarification.question = None

    # -------------------------------------------------
    # CONTINUE GRAPH EXECUTION
    # -------------------------------------------------

    result = await graph.ainvoke(

        workflow_state,

        config=config
    )

    return result
