from datetime import datetime

from app.core.graph.state import (
    CopilotState
)

from app.db.registry import (
    get_database_url
)

from app.core.intent import (
    extract_intent
)

from app.core.sql.builder import (
    build_sql_query
)

from app.core.sql.validator import (
    validate_sql_query
)

from app.core.sql.executor import (
    execute_sql_query
)

from app.models.state import (
    QueryPlan
)

from app.platform.repository import (
    save_workflow_run
)

from app.core.policies.engine import (
    evaluate_sql_policies
)


from app.core.cost.analyzer import (
    analyze_query_cost
)


from app.core.sql.normalizer import (
    normalize_sql
)

from app.core.policies.rbac import (
    authorize_operation
)

import json

from app.platform.memory import (
    get_conversation_memory,
    save_conversation_memory
)


from app.core.clarification.engine import (
    analyze_clarification
)

from app.core.graph.status import (
    WorkflowStatus
)

from app.core.planner import (
    generate_query_plan
)

from app.core.sql.explainer import (
    explain_sql
)


async def load_memory_node(
    state: CopilotState
) -> CopilotState:

    thread_id = state.session_id

    memory = await get_conversation_memory(
        thread_id
    )

    # -------------------------------------------------
    # NO MEMORY FOUND
    # -------------------------------------------------

    if not memory:

        state.conversation_memory = None

        state.node_trace.append(
            "load_memory_node"
        )

        state.updated_at = datetime.utcnow()

        return state

    # -------------------------------------------------
    # MEMORY FOUND
    # -------------------------------------------------

    conversation_memory = {

        "active_table":
            memory.active_table,

        "selected_columns":
            json.loads(
                memory.selected_columns
            )
            if memory.selected_columns
            else [],

        "active_filters":
            json.loads(
                memory.active_filters
            )
            if memory.active_filters
            else {},

        "order_by":
            json.loads(
                memory.order_by
            )
            if memory.order_by
            else [],

        "row_limit":
            memory.row_limit,

        "last_generated_sql":
            memory.last_generated_sql,

        "last_user_prompt":
            memory.last_user_prompt
    }

    state.conversation_memory = (
        conversation_memory
    )

    state.updated_at = datetime.utcnow()

    state.node_trace.append(
        "load_memory_node"
    )

    return state


async def extract_intent_node(
    state: CopilotState
) -> CopilotState:
    
    # -------------------------------------------------
    # SKIP ON RESUME
    # -------------------------------------------------

    if state.is_resumed:

        state.node_trace.append(
            "intent_extraction_skipped_on_resume"
        )

        return state

    extracted_intent = await extract_intent(

        prompt=state.user_prompt,

        memory=state.conversation_memory
    )

    state.extracted_intent = (
        extracted_intent
    )

    state.updated_at = datetime.utcnow()

    state.node_trace.append(
        "extract_intent_node"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state



async def clarification_node(
    state: CopilotState
) -> CopilotState:
    

    # -----------------------------------------
    # SKIP CLARIFICATION ON RESUME
    # -----------------------------------------

    if state.is_resumed:

        state.node_trace.append(
            "clarification_skipped_on_resume"
        )

        return state

    intent = state.extracted_intent

    # -----------------------------------------
    # SAFETY CHECK
    # -----------------------------------------

    if not intent:

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.errors.append(
            "No extracted intent found."
        )

        state.node_trace.append(
            "clarification_node_failed"
        )

        return state

    # -----------------------------------------
    # CLARIFICATION ANALYSIS
    # -----------------------------------------

    clarification_result = (
        analyze_clarification(intent)
    )

    # -----------------------------------------
    # NEEDS CLARIFICATION
    # -----------------------------------------

    if clarification_result.requires_clarification:

        state.workflow_status = (
            WorkflowStatus.WAITING_FOR_CLARIFICATION
        )

        state.clarification.required = True

        state.clarification.question = (
            clarification_result.question
        )

        state.clarification.missing_fields = (
            clarification_result.missing_fields
        )

        state.clarification.resume_from_node = (
            "generate_query_plan_node"
        )
        state.updated_at = datetime.utcnow()

        state.node_trace.append(
            "clarification_required"
        )


        await save_workflow_run(
            state.model_dump()
        )

        return state

    # -----------------------------------------
    # CONTINUE WORKFLOW
    # -----------------------------------------

    state.workflow_status = (
        WorkflowStatus.RUNNING
    )

    state.clarification.required = False

    state.updated_at = datetime.utcnow()

    state.node_trace.append(
        "clarification_completed"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state




async def generate_query_plan_node(
    state: CopilotState
) -> CopilotState:

    try:

        extracted_intent = (
            state.extracted_intent
        )

        schema_context = (
            state.schema_context
        )

        # -------------------------------------------------
        # SAFETY CHECKS
        # -------------------------------------------------

        if not extracted_intent:

            raise ValueError(
                "No extracted intent found"
            )

        if not schema_context:

            raise ValueError(
                "No schema context found"
            )

        print(
            "PLANNER INPUT:",
            extracted_intent.model_dump()
        )

        # -------------------------------------------------
        # GENERATE QUERY PLAN
        # -------------------------------------------------

        query_plan_obj = await generate_query_plan(

            extracted_intent=
                extracted_intent,

            schema_context=
                schema_context
        )

        print(
            "QUERY PLAN:",
            query_plan_obj.model_dump()
        )

        # -------------------------------------------------
        # GENERATE SQL
        # -------------------------------------------------

        raw_sql = build_sql_query(
            query_plan_obj
        )

        print(
            "RAW SQL:",
            raw_sql
        )

        normalized_sql = normalize_sql(
            raw_sql
        )

        print(
            "NORMALIZED SQL:",
            normalized_sql
        )

        # -------------------------------------------------
        # EXPLAIN SQL
        # -------------------------------------------------

        sql_explanation = explain_sql(
            normalized_sql
        )

        print(
            "SQL EXPLANATION:",
            sql_explanation
        )

        # -------------------------------------------------
        # UPDATE STATE
        # -------------------------------------------------

        state.query_plan = (
            query_plan_obj
        )

        state.generated_sql = (
            normalized_sql
        )

        state.sql_explanation = (
            sql_explanation
        )

        state.errors = []

        state.updated_at = (
            datetime.utcnow()
        )

        state.node_trace.append(
            "generate_query_plan_node"
        )

        await save_workflow_run(
            state.model_dump()
        )

        return state

    except Exception as e:

        print(
            "PLANNER ERROR:",
            str(e)
        )

        state.query_plan = None

        state.generated_sql = None

        state.validation_result = None

        state.risk_level = None

        state.execution_result = None

        state.errors.append(
            str(e)
        )

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.updated_at = (
            datetime.utcnow()
        )

        state.node_trace.append(
            "generate_query_plan_node_failed"
        )

        await save_workflow_run(
            state.model_dump()
        )

        return state


async def validate_sql_node(
    state: CopilotState
) -> CopilotState:

    # -----------------------------------------
    # STOP IF PREVIOUS FAILURE
    # -----------------------------------------

    if state.errors:

        return state

    sql = state.generated_sql

    schema_context = (
        state.schema_context
    )

    if not sql:

        state.errors.append(
            "No SQL generated."
        )

        return state

    # -----------------------------------------
    # SQL VALIDATION
    # -----------------------------------------

    validation_result = (
        validate_sql_query(
            sql=sql,
            schema_context=schema_context
        )
    )

    # -------------------------------------------------
    # LIMIT SAFETY
    # -------------------------------------------------

    operation = None

    if state.query_plan:

        operation = (
            state.query_plan.operation
        )

    elif sql.strip().upper().startswith("SELECT"):

        operation = "SELECT"

    if operation == "SELECT":

        if (
            state.query_plan
            and
            state.query_plan.limit is None
        ):

            validation_result.warnings.append(
                "SELECT query without LIMIT detected"
            )

    print(
        "VALIDATION RESULT:",
        validation_result.model_dump()
    )

    state.validation_result = (
        validation_result
    )

    # -----------------------------------------
    # VALIDATION FAILED
    # -----------------------------------------

    if not validation_result.passed:

        state.risk_level = "blocked"

        state.errors.extend(
            validation_result.errors
        )

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.updated_at = (
            datetime.utcnow()
        )

        state.node_trace.append(
            "validate_sql_node_failed"
        )

        await save_workflow_run(
            state.model_dump()
        )

        return state

    # -----------------------------------------
    # POLICY ENGINE
    # -----------------------------------------

    policy_result = (
        evaluate_sql_policies(sql)
    )

    # -----------------------------------------
    # BLOCKED
    # -----------------------------------------

    if not policy_result.allowed:

        state.risk_level = "blocked"

        state.errors.extend(
            policy_result.errors
        )

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.updated_at = (
            datetime.utcnow()
        )

        state.node_trace.append(
            "validate_sql_node_policy_blocked"
        )

        await save_workflow_run(
            state.model_dump()
        )

        return state

    # -----------------------------------------
    # SUCCESS
    # -----------------------------------------

    state.risk_level = (
        policy_result.risk_level
    )

    state.updated_at = (
        datetime.utcnow()
    )

    state.node_trace.append(
        "validate_sql_node"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state



# =========================================================
# AUTHORIZE QUERY NODE
# =========================================================

async def authorize_query_node(
    state: CopilotState
) -> CopilotState:

    # -------------------------------------------------
    # STOP IF EXISTING ERRORS
    # -------------------------------------------------

    if state.errors:

        return state

    # -------------------------------------------------
    # REQUIRE QUERY PLAN
    # -------------------------------------------------

    if not state.query_plan:

        state.errors.append(
            "Missing query plan for authorization."
        )

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.node_trace.append(
            "authorize_query_node_failed"
        )

        return state

    # -------------------------------------------------
    # EXTRACT ROLE
    # -------------------------------------------------

    role = (
        state.user_role
        or "analyst"
    )

    # -------------------------------------------------
    # EXTRACT OPERATION
    # -------------------------------------------------

    operation = (
        state.query_plan.operation
    )

    # -------------------------------------------------
    # AUTHORIZE
    # -------------------------------------------------

    auth_result = authorize_operation(

        role=role,

        operation=operation
    )

    # -------------------------------------------------
    # BLOCKED
    # -------------------------------------------------

    if not auth_result["allowed"]:

        state.errors.append(
            auth_result["reason"]
        )

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.risk_level = "blocked"

        state.updated_at = (
            datetime.utcnow()
        )

        state.node_trace.append(
            "authorize_query_blocked"
        )

        await save_workflow_run(
            state.model_dump()
        )

        return state

    # -------------------------------------------------
    # SUCCESS
    # -------------------------------------------------

    state.updated_at = (
        datetime.utcnow()
    )

    state.node_trace.append(
        "authorize_query_node"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state




async def classify_risk_node(
    state: CopilotState
) -> CopilotState:

    # -------------------------------------------------
    # STOP ON EXISTING ERRORS
    # -------------------------------------------------

    if state.errors:

        return state

    sql = state.generated_sql

    query_plan = state.query_plan

    if not sql:

        return state

    # -------------------------------------------------
    # COST ANALYSIS
    # -------------------------------------------------

    database_url = await get_database_url(

        tenant_id=state.tenant_id,

        user_id=state.user_id,

        connection_ref=state.connection_ref
    )

    cost_analysis = (
        await analyze_query_cost(

            database_url=database_url,

            sql=sql
        )
    )

    state.cost_analysis = (
        cost_analysis
    )

    # -------------------------------------------------
    # DEFAULT RISK
    # -------------------------------------------------

    risk_level = "low"

    if query_plan:

        operation = (
            query_plan.operation.upper()
        )

    else:

        sql_upper = sql.strip().upper()

        if sql_upper.startswith("SELECT"):

            operation = "SELECT"

        elif sql_upper.startswith("UPDATE"):

            operation = "UPDATE"

        elif sql_upper.startswith("DELETE"):

            operation = "DELETE"

        elif sql_upper.startswith("INSERT"):

            operation = "INSERT"

        else:

            operation = "UNKNOWN"

    # -------------------------------------------------
    # DELETE SAFETY
    # -------------------------------------------------

    if operation == "DELETE":

        sql_upper = sql.upper()

        if "WHERE" not in sql_upper:

            risk_level = "blocked"

        else:

            risk_level = "high"

    # -------------------------------------------------
    # UPDATE SAFETY
    # -------------------------------------------------

    elif operation == "UPDATE":

        sql_upper = sql.upper()

        if "WHERE" not in sql_upper:

            risk_level = "blocked"

        else:

            risk_level = "medium"

    # -------------------------------------------------
    # INSERT SAFETY
    # -------------------------------------------------

    elif operation == "INSERT":

        risk_level = "medium"

    # -------------------------------------------------
    # SELECT SAFETY
    # -------------------------------------------------

    elif operation == "SELECT":

        risk_level = "low"

        if query_plan:

            if len(query_plan.joins) >= 3:

                risk_level = "medium"

            if query_plan.unions:

                risk_level = "medium"

            if query_plan.ctes:

                risk_level = "medium"

    # -------------------------------------------------
    # COST ESCALATION
    # -------------------------------------------------

    if cost_analysis.success:

        estimated_cost = (
            cost_analysis.estimated_cost
        )

        if estimated_cost > 1000:

            risk_level = "high"

    # -------------------------------------------------
    # FINAL STATE UPDATE
    # -------------------------------------------------

    state.risk_level = risk_level

    state.updated_at = (
        datetime.utcnow()
    )

    state.node_trace.append(
        "classify_risk_node"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state



async def request_sql_review_node(
    state
):

    # -----------------------------------------
    # RESUME FLOW
    # -----------------------------------------

    if state.is_resumed:

        state.node_trace.append(
            "sql_review_resumed"
        )

        return state

    # -----------------------------------------
    # FIRST PASS
    # -----------------------------------------

    state.workflow_status = (
        WorkflowStatus.WAITING_FOR_SQL_REVIEW
    )

    state.approval.required = True

    state.approval.approved = False

    state.updated_at = (
        datetime.utcnow()
    )

    state.node_trace.append(
        "sql_review_requested"
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state

# async def request_human_approval_node(
#     state: CopilotState
# ) -> CopilotState:

#     # -------------------------------------------------
#     # STOP IF BLOCKED
#     # -------------------------------------------------

#     if state.risk_level == "blocked":

#         state.workflow_status = (
#             WorkflowStatus.FAILED
#         )

#         state.errors.append(
#             "Query blocked by safety policy."
#         )

#         state.node_trace.append(
#             "approval_blocked"
#         )

#         await save_workflow_run(
#             state.model_dump()
#         )

#         return state

#     # -------------------------------------------------
#     # SKIP APPROVAL ON RESUME
#     # -------------------------------------------------

#     if state.is_resumed:

#         if state.approval.approved:

#             state.node_trace.append(
#                 "approval_skipped_on_resume"
#             )

#             return state

#         state.workflow_status = (
#             WorkflowStatus.REJECTED
#         )

#         state.node_trace.append(
#             "approval_rejected"
#         )

#         return state

#     # -------------------------------------------------
#     # LOW RISK
#     # AUTO APPROVE
#     # -------------------------------------------------

#     if state.risk_level == "low":

#         state.approval.required = False

#         state.approval.approved = True

#         state.workflow_status = (
#             WorkflowStatus.APPROVED
#         )

#     # -------------------------------------------------
#     # MEDIUM/HIGH RISK
#     # REQUIRE HUMAN APPROVAL
#     # -------------------------------------------------

#     else:

#         state.approval.required = True

#         state.approval.approved = False

#         state.workflow_status = (
#             WorkflowStatus.WAITING_FOR_APPROVAL
#         )

#     # -------------------------------------------------
#     # UPDATE STATE
#     # -------------------------------------------------

#     state.updated_at = (
#         datetime.utcnow()
#     )

#     state.node_trace.append(
#         "request_human_approval_node"
#     )

#     await save_workflow_run(
#         state.model_dump()
#     )

#     return state

async def execute_query_node(
    state: CopilotState
) -> CopilotState:

    if state.errors:

        return state

    sql = state.generated_sql

    if not sql:

        return state
    
    # -------------------------------------------------
    # APPROVAL CHECK
    # -------------------------------------------------

    # -------------------------------------------------
    # SQL REVIEW CHECK
    # -------------------------------------------------

    if state.approval.required:

        if not state.approval.approved:

            state.workflow_status = (
                WorkflowStatus.WAITING_FOR_SQL_REVIEW
            )

            return state

    database_url = await get_database_url(

        tenant_id=state.tenant_id,

        user_id=state.user_id,

        connection_ref=state.connection_ref
    )

    print(
        "EXECUTING SQL:",
        sql
    )

    execution_result = (
        await execute_sql_query(

            database_url=database_url,

            sql=sql
        )
    )

    state.execution_result = (
        execution_result
    )


    if execution_result.success:

        state.workflow_status = (
            WorkflowStatus.COMPLETED
        )

    else:

        state.workflow_status = (
            WorkflowStatus.FAILED
        )

        state.errors.append(
            execution_result.error
        )

    state.updated_at = (
        datetime.utcnow()
    )

    if execution_result.success:

        state.node_trace.append(
            "execute_query_node"
        )

    else:

        state.node_trace.append(
            "execute_query_node_failed"
        )

    print(
        "EXECUTION RESULT:",
        execution_result.model_dump()
    )

    await save_workflow_run(
        state.model_dump()
    )

    return state


