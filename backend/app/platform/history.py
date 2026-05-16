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

        return workflow