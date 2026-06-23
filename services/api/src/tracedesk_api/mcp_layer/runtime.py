from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine
from tracedesk_api.mcp_layer.contracts import (
    AuthorizationContext,
    ServiceName,
    ToolMeta,
    ToolResponse,
)


@lru_cache
def mcp_engine() -> AsyncEngine:
    return create_engine(get_settings())


def response(
    service: ServiceName,
    context: AuthorizationContext,
    data: dict[str, object] | list[object],
    *,
    idempotent_replay: bool = False,
) -> ToolResponse:
    return ToolResponse(
        data=data,
        meta=ToolMeta(
            service=service,
            request_id=context.request_id,
            idempotent_replay=idempotent_replay,
        ),
    )
