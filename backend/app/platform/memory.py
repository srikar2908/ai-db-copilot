import json

from sqlalchemy import select

from app.platform.database import (
    AsyncSessionLocal
)

from app.platform.models import (
    ConversationMemory
)


# -------------------------------------------------
# GET MEMORY
# -------------------------------------------------

async def get_conversation_memory(
    thread_id: str
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(ConversationMemory).where(

                ConversationMemory.thread_id
                == thread_id
            )
        )

        return result.scalar_one_or_none()


# -------------------------------------------------
# SAVE MEMORY
# -------------------------------------------------

async def save_conversation_memory(

    thread_id: str,

    tenant_id: str,

    user_id: str,

    active_table: str,

    selected_columns: list,

    active_filters: list,

    order_by: list,

    row_limit: int,

    last_generated_sql: str,

    last_user_prompt: str
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(

            select(ConversationMemory).where(

                ConversationMemory.thread_id
                == thread_id
            )
        )

        memory = result.scalar_one_or_none()

        if memory:

            memory.active_table = active_table

            memory.selected_columns = json.dumps(
                selected_columns
            )

            memory.active_filters = json.dumps(
                active_filters
            )

            memory.order_by = json.dumps(
                order_by
            )

            memory.row_limit = row_limit

            memory.last_generated_sql = (
                last_generated_sql
            )

            memory.last_user_prompt = (
                last_user_prompt
            )

        else:

            memory = ConversationMemory(

                thread_id=thread_id,

                tenant_id=tenant_id,

                user_id=user_id,

                active_table=active_table,

                selected_columns=json.dumps(
                    selected_columns
                ),

                active_filters=json.dumps(
                    active_filters
                ),

                order_by=json.dumps(
                    order_by
                ),

                row_limit=row_limit,

                last_generated_sql=
                    last_generated_sql,

                last_user_prompt=
                    last_user_prompt
            )

            session.add(memory)

        await session.commit()