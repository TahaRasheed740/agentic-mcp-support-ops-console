from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import get_settings
from tracedesk_api.dependencies import get_engine
from tracedesk_api.models import DemoSession, SupportPersona, TicketOverlay
from tracedesk_api.schemas import DemoSessionView, Persona, SessionCreate
from tracedesk_api.security import sign_session_id, verify_session_token

router = APIRouter(prefix="/api/v1", tags=["demo sessions"])


@router.get("/personas", response_model=list[Persona])
async def list_personas(engine: AsyncEngine = Depends(get_engine)) -> list[Persona]:
    async with engine.connect() as connection:
        rows = (
            await connection.execute(select(SupportPersona).order_by(SupportPersona.name))
        ).mappings()
        return [Persona.model_validate(row) for row in rows]


@router.post("/sessions", response_model=DemoSessionView, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    response: Response,
    engine: AsyncEngine = Depends(get_engine),
) -> DemoSessionView:
    session_id = str(uuid4())
    created_at = datetime.now(UTC)
    async with engine.begin() as connection:
        persona_row = (
            (
                await connection.execute(
                    select(SupportPersona).where(SupportPersona.id == payload.persona_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if persona_row is None:
            raise HTTPException(status_code=404, detail="Support persona not found")
        await connection.execute(
            insert(DemoSession).values(
                id=session_id,
                persona_id=payload.persona_id,
                created_at=created_at,
                reset_at=None,
            )
        )
    settings = get_settings()
    response.set_cookie(
        "tracedesk_session",
        sign_session_id(session_id, settings.session_secret),
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=60 * 60 * 8,
    )
    return DemoSessionView(
        id=session_id,
        persona=Persona.model_validate(persona_row),
        created_at=created_at,
        reset_at=None,
    )


@router.get("/sessions/current", response_model=DemoSessionView)
async def current_session(
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> DemoSessionView:
    session_id = verify_session_token(tracedesk_session, get_settings().session_secret)
    if session_id is None:
        raise HTTPException(status_code=404, detail="No active demo session")
    async with engine.connect() as connection:
        row = (
            (
                await connection.execute(
                    select(
                        DemoSession.id,
                        DemoSession.created_at,
                        DemoSession.reset_at,
                        SupportPersona.id.label("persona_id"),
                        SupportPersona.name,
                        SupportPersona.role,
                        SupportPersona.initials,
                        SupportPersona.specialty,
                    )
                    .join(SupportPersona, DemoSession.persona_id == SupportPersona.id)
                    .where(DemoSession.id == session_id)
                )
            )
            .mappings()
            .one_or_none()
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Demo session expired")
    return _session_from_row(row)


@router.post("/sessions/{session_id}/reset", response_model=DemoSessionView)
async def reset_session(
    session_id: str,
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> DemoSessionView:
    signed_session_id = verify_session_token(tracedesk_session, get_settings().session_secret)
    if signed_session_id != session_id:
        raise HTTPException(status_code=403, detail="Session token does not match")
    reset_at = datetime.now(UTC)
    async with engine.begin() as connection:
        await connection.execute(
            delete(TicketOverlay).where(TicketOverlay.session_id == session_id)
        )
        updated = await connection.execute(
            update(DemoSession)
            .where(DemoSession.id == session_id)
            .values(reset_at=reset_at)
            .returning(DemoSession.persona_id, DemoSession.created_at)
        )
        session_row = updated.mappings().one_or_none()
        if session_row is None:
            raise HTTPException(status_code=404, detail="Demo session not found")
        persona_row = (
            (
                await connection.execute(
                    select(SupportPersona).where(SupportPersona.id == session_row["persona_id"])
                )
            )
            .mappings()
            .one()
        )
    return DemoSessionView(
        id=session_id,
        persona=Persona.model_validate(persona_row),
        created_at=session_row["created_at"],
        reset_at=reset_at,
    )


def _session_from_row(row: Any) -> DemoSessionView:
    persona = Persona(
        id=str(row["persona_id"]),
        name=str(row["name"]),
        role=str(row["role"]),
        initials=str(row["initials"]),
        specialty=str(row["specialty"]),
    )
    return DemoSessionView(
        id=str(row["id"]),
        persona=persona,
        created_at=cast(datetime, row["created_at"]),
        reset_at=cast(datetime | None, row["reset_at"]),
    )
