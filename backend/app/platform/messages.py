import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.platform.database import AsyncSessionLocal
from app.platform.models import ConversationMessage


logger = logging.getLogger(__name__)


async def append_conversation_message(
    *,
    thread_id: str,
    tenant_id: str,
    user_id: str,
    role: str,
    content: dict,
) -> ConversationMessage | None:
    message = ConversationMessage(
        id=str(uuid4()),
        thread_id=thread_id,
        tenant_id=tenant_id,
        user_id=str(user_id),
        role=role,
        content=content,
    )

    async with AsyncSessionLocal() as session:
        try:
            session.add(message)
            await session.commit()
            return message
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Conversation message write failed")
            return None


async def list_conversation_messages(
    *,
    thread_id: str,
    tenant_id: str,
    user_id: str,
    limit: int = 100,
) -> list[ConversationMessage]:
    async with AsyncSessionLocal() as session:
        try:
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
        except SQLAlchemyError:
            logger.exception("Conversation message read failed")
            return []
