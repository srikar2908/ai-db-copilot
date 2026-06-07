from sqlalchemy.exc import ProgrammingError

from app.platform import messages


class BrokenSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    def add(self, _):
        return None

    async def commit(self):
        raise ProgrammingError("insert", {}, Exception("missing table"))

    async def rollback(self):
        return None


async def test_message_write_failure_does_not_break_query(monkeypatch):
    monkeypatch.setattr(messages, "AsyncSessionLocal", BrokenSession)

    result = await messages.append_conversation_message(
        thread_id="thread-1",
        tenant_id="tenant-1",
        user_id="1",
        role="user",
        content={"text": "show employees"},
    )

    assert result is None
