from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from tracedesk_api.main import app


@asynccontextmanager
async def client_with_engine(engine: object) -> AsyncIterator[AsyncClient]:
    app.state.engine = engine
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_liveness_does_not_require_database() -> None:
    async with client_with_engine(object()) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


@pytest.mark.asyncio
async def test_readiness_reports_connected_database() -> None:
    engine = object()
    with patch("tracedesk_api.main.database_is_ready", new=AsyncMock()) as check:
        async with client_with_engine(engine) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "api",
        "database": "connected",
    }
    check.assert_awaited_once_with(engine)


@pytest.mark.asyncio
async def test_readiness_reports_database_failure() -> None:
    from sqlalchemy.exc import OperationalError

    failure = OperationalError("SELECT 1", {}, Exception("offline"))
    with patch("tracedesk_api.main.database_is_ready", new=AsyncMock(side_effect=failure)):
        async with client_with_engine(object()) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
