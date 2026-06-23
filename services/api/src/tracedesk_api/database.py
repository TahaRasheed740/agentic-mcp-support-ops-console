from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tracedesk_api.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@asynccontextmanager
async def database_lifespan(engine: AsyncEngine) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await engine.dispose()


async def database_is_ready(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
