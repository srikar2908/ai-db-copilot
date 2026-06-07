from fastapi import APIRouter, Depends

from sqlalchemy import desc, select

from app.platform.repository import (
    get_all_workflows,
    get_workflow_by_thread
)
from app.platform.database import AsyncSessionLocal
from app.platform.models import WorkflowRun
from app.security.dependencies import get_current_user
from app.platform.messages import list_conversation_messages

router = APIRouter()


@router.get("/history")
async def list_history(
    current_user=Depends(get_current_user)
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.tenant_id == current_user["tenant_id"],
                *(
                    [WorkflowRun.user_id == str(current_user["user_id"])]
                    if current_user["role"] != "admin"
                    else []
                )
            )
            .order_by(desc(WorkflowRun.created_at))
            .limit(50)
        )

        workflows = result.scalars().all()

        return [
            {
                "thread_id":
                    workflow.thread_id,

                "user_prompt":
                    workflow.user_prompt,

                "generated_sql":
                    workflow.generated_sql,

                "approval_status":
                    workflow.approval_status,

                "created_at":
                    workflow.created_at,

                "risk_level":
                    workflow.risk_level,

                "execution_status":
                    workflow.execution_status,

                "execution_result":
                    workflow.execution_result,

                "validation_result":
                    workflow.validation_result,

                "errors":
                    workflow.errors
            }
            for workflow in workflows
        ]


@router.get("/threads")
async def list_threads(
    current_user=Depends(get_current_user)
):

    workflows = await get_all_workflows(
        tenant_id=current_user["tenant_id"],
        user_id=(
            None
            if current_user["role"] == "admin"
            else current_user["user_id"]
        ),
    )

    return workflows


@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    current_user=Depends(get_current_user)
):

    workflow = await get_workflow_by_thread(
        thread_id,
        tenant_id=current_user["tenant_id"],
        user_id=(
            None
            if current_user["role"] == "admin"
            else current_user["user_id"]
        ),
    )

    if not workflow:

        return {
            "error":
                "Thread not found"
        }

    return workflow


@router.get("/thread/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    current_user=Depends(get_current_user),
):
    messages = await list_conversation_messages(
        thread_id=thread_id,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
    )

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]
