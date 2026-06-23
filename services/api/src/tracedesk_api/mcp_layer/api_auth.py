from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import get_settings
from tracedesk_api.mcp_layer.contracts import AuthorizationContext
from tracedesk_api.models import DemoSession
from tracedesk_api.security import verify_session_token


async def authorization_for_request(
    token: str | None,
    engine: AsyncEngine,
) -> AuthorizationContext:
    session_id = verify_session_token(token, get_settings().session_secret)
    persona_id = "persona_maya"
    if session_id:
        async with engine.connect() as connection:
            stored_persona = await connection.scalar(
                select(DemoSession.persona_id).where(DemoSession.id == session_id)
            )
        if stored_persona:
            persona_id = str(stored_persona)
        else:
            session_id = None
    return AuthorizationContext(
        request_id=f"req_{uuid4().hex}",
        persona_id=persona_id,
        session_id=session_id,
        scopes=["knowledge:read", "operations:read", "support:read", "support:write"],
        approved_action_ids=[],
    )
