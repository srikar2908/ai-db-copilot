from fastapi import APIRouter

from app.platform.repository import (
    get_all_workflows,
    get_workflow_by_thread
)

router = APIRouter()


@router.get("/threads")
async def list_threads():

    workflows = await get_all_workflows()

    return workflows


@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str
):

    workflow = await get_workflow_by_thread(
        thread_id
    )

    if not workflow:

        return {
            "error":
                "Thread not found"
        }

    return workflow