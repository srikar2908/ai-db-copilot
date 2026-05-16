import asyncio

from app.platform.database import (
    engine,
    Base
)

from app.platform import models


async def init():

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )

    print(
        "Platform DB initialized"
    )


asyncio.run(init())