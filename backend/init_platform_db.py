import asyncio

from app.platform.schema import ensure_platform_schema


async def init():

    await ensure_platform_schema()

    print(
        "Platform DB initialized"
    )


asyncio.run(init())
