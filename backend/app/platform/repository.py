from datetime import datetime

from sqlalchemy import select

from app.platform.database import (
    AsyncSessionLocal
)

from app.platform.models import (
    WorkflowRun
)

import json


# -------------------------------------------------
# SAFE ACCESSOR
# -------------------------------------------------

def safe_get(

    obj,

    key,

    default=None
):

    if obj is None:

        return default

    # ---------------------------------------------
    # DICT
    # ---------------------------------------------

    if isinstance(obj, dict):

        return obj.get(
            key,
            default
        )

    # ---------------------------------------------
    # PYDANTIC / OBJECT
    # ---------------------------------------------

    return getattr(
        obj,
        key,
        default
    )


# -------------------------------------------------
# SAVE WORKFLOW RUN
# -------------------------------------------------

# -------------------------------------------------
# SAVE WORKFLOW RUN
# -------------------------------------------------

async def save_workflow_run(
    state
):

    async with AsyncSessionLocal() as session:

        existing = await session.get(

            WorkflowRun,

            state["session_id"]
        )

        # -----------------------------------------
        # EXECUTION STATUS
        # -----------------------------------------

        execution_result = state.get(
            "execution_result"
        )

        execution_status = None

        if execution_result:

            success = safe_get(

                execution_result,

                "success",

                False
            )

            execution_status = (
                "success"
                if success
                else "failed"
            )

        # -----------------------------------------
        # COMMON DATA
        # -----------------------------------------

        approval = state.get(
            "approval"
        )

        common_fields = {

            "generated_sql":
                state.get(
                    "generated_sql"
                ),

            "original_generated_sql":
                state.get(
                    "original_generated_sql"
                ),

            "approved_sql":
                state.get(
                    "approved_sql"
                ),

            "approval_status":
                safe_get(
                    approval,
                    "approved"
                ),

            "risk_level":
                state.get(
                    "risk_level"
                ),

            "execution_status":
                execution_status,

            "review_result":
                state.get(
                    "review_result"
                ),

            "validation_result":
                state.get(
                    "validation_result"
                ),

            "execution_result":
                json.loads(
                    json.dumps(
                        state.get(
                            "execution_result"
                        ),
                        default=str
                    )
                ),

            "node_trace":
                state.get(
                    "node_trace"
                ),

            "errors":
                state.get(
                    "errors"
                ),

            "approval_timestamp":
                state.get(
                    "approval_timestamp"
                ),

            "updated_at":
                datetime.utcnow()
        }

        # -----------------------------------------
        # UPDATE
        # -----------------------------------------

        if existing:

            for key, value in common_fields.items():

                setattr(
                    existing,
                    key,
                    value
                )

        # -----------------------------------------
        # CREATE
        # -----------------------------------------

        else:

            workflow = WorkflowRun(

                thread_id=state[
                    "session_id"
                ],

                tenant_id=state[
                    "tenant_id"
                ],

                user_id=state[
                    "user_id"
                ],

                connection_ref=state[
                    "connection_ref"
                ],

                user_prompt=state[
                    "user_prompt"
                ],

                created_at=datetime.utcnow(),

                **common_fields
            )

            session.add(
                workflow
            )

        await session.commit()


# -------------------------------------------------
# GET SINGLE WORKFLOW
# -------------------------------------------------

async def get_workflow_run(
    thread_id: str
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(WorkflowRun).where(

                WorkflowRun.thread_id
                == thread_id
            )
        )

        return result.scalar_one_or_none()


# -------------------------------------------------
# GET ALL WORKFLOWS
# -------------------------------------------------

async def get_all_workflows():

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(WorkflowRun)
        )

        workflows = (
            result.scalars().all()
        )

        return [

            {

                "thread_id":
                    workflow.thread_id,

                "tenant_id":
                    workflow.tenant_id,

                "user_prompt":
                    workflow.user_prompt,

                "generated_sql":
                    workflow.generated_sql,

                "approval_status":
                    workflow.approval_status,

                "risk_level":
                    workflow.risk_level,

                "execution_status":
                    workflow.execution_status,

                "created_at":
                    workflow.created_at,

                "updated_at":
                    workflow.updated_at
            }

            for workflow in workflows
        ]


# -------------------------------------------------
# GET WORKFLOW BY THREAD
# -------------------------------------------------

async def get_workflow_by_thread(
    thread_id: str
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(WorkflowRun).where(

                WorkflowRun.thread_id
                == thread_id
            )
        )

        workflow = (
            result.scalar_one_or_none()
        )

        if not workflow:

            return None

        return {

            "thread_id":
                workflow.thread_id,

            "tenant_id":
                workflow.tenant_id,

            "user_id":
                workflow.user_id,

            "connection_ref":
                workflow.connection_ref,

            "user_prompt":
                workflow.user_prompt,

            "generated_sql":
                workflow.generated_sql,

            "approval_status":
                workflow.approval_status,

            "risk_level":
                workflow.risk_level,

            "execution_status":
                workflow.execution_status,

            "created_at":
                workflow.created_at,

            "updated_at":
                workflow.updated_at
        }