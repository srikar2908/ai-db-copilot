from uuid import uuid4

from sqlalchemy import select

from app.platform.database import AsyncSessionLocal
from app.platform.models import ConversationMessage


async def append_conversation_message(
    *,
    thread_id: str,
    tenant_id: str,
    user_id: str,
    role: str,
    content: dict,
) -> ConversationMessage:
    message = ConversationMessage(
        id=str(uuid4()),
        thread_id=thread_id,
        tenant_id=tenant_id,
        user_id=str(user_id),
        role=role,
        content=content,
    )

    async with AsyncSessionLocal() as session:
        session.add(message)
        await session.commit()
        return message


async def list_conversation_messages(
    *,
    thread_id: str,
    tenant_id: str,
    user_id: str,
    limit: int = 100,
) -> list[ConversationMessage]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationMessage)
            .where(
                ConversationMessage.thread_id == thread_id,
                ConversationMessage.tenant_id == tenant_id,
                ConversationMessage.user_id == str(user_id),
            )
            .order_by(ConversationMessage.created_at.asc())
            .limit(min(limit, 200))
        )
        return list(result.scalars().all())
