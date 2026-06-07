from sqlalchemy import select

from app.platform.database import (
    AsyncSessionLocal
)

from app.platform.models import (
    WorkflowRun
)


# -------------------------------------------------
# GET WORKFLOW RUN
# -------------------------------------------------

async def get_workflow_run(
    thread_id: str,
    tenant_id: str,
    user_id: str | None = None
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id,
                WorkflowRun.tenant_id == tenant_id,
                *(
                    [WorkflowRun.user_id == str(user_id)]
                    if user_id is not None
                    else []
                )
            )
        )

        workflow = (
            result.scalar_one_or_none()
        )

        return workflow
