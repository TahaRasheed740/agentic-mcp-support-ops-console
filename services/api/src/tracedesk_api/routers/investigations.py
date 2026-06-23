from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import get_settings
from tracedesk_api.dependencies import get_engine
from tracedesk_api.investigations.manager import InvestigationManager
from tracedesk_api.investigations.repository import InvestigationRepository
from tracedesk_api.investigations.schemas import (
    ActionRejection,
    InvestigationCreate,
    InvestigationCreated,
    InvestigationListItem,
    InvestigationView,
    ProposedAction,
)
from tracedesk_api.mcp_layer.api_auth import authorization_for_request
from tracedesk_api.mcp_layer.gateway import MCPGateway

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_investigation(
    body: InvestigationCreate,
    request: Request,
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> InvestigationCreated:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live investigations require ANTHROPIC_API_KEY",
        )
    authorization = await authorization_for_request(tracedesk_session, engine)
    manager: InvestigationManager = request.app.state.investigation_manager
    try:
        investigation_id = await manager.create(body.case_id, authorization)
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return InvestigationCreated(id=investigation_id, status="queued")


@router.get("", response_model=list[InvestigationListItem])
async def list_investigations(
    limit: int = Query(default=25, ge=1, le=100),
    engine: AsyncEngine = Depends(get_engine),
) -> list[InvestigationListItem]:
    return await InvestigationRepository(engine).list_recent(limit=limit)


@router.post(
    "/{investigation_id}/actions/{action_id}/approve",
    response_model=ProposedAction,
)
async def approve_action(
    investigation_id: str,
    action_id: str,
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> ProposedAction:
    repository = InvestigationRepository(engine)
    action = await repository.get_action(investigation_id, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Proposed action not found")
    if action.status != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action.status}")
    authorization = await authorization_for_request(tracedesk_session, engine)
    if authorization.session_id is None:
        await repository.mark_action_status(
            investigation_id,
            action_id,
            "stale",
            error="Approved writes require an isolated demo session",
        )
        raise HTTPException(status_code=409, detail="Approved writes require an active demo session")
    approved_authorization = authorization.model_copy(
        update={"approved_action_ids": [action_id]}
    )
    await repository.mark_action_status(investigation_id, action_id, "approved")
    arguments = dict(action.arguments)
    arguments["approval_id"] = action_id
    arguments["idempotency_key"] = f"approval:{action.id}"
    try:
        result = await MCPGateway(get_settings()).call_tool(
            action.service,
            action.tool_name,
            arguments,
            approved_authorization,
        )
    except Exception as error:
        return await repository.mark_action_status(
            investigation_id,
            action_id,
            "failed",
            error=str(error),
        )
    return await repository.mark_action_status(
        investigation_id,
        action_id,
        "executed",
        result=result,
    )


@router.post(
    "/{investigation_id}/actions/{action_id}/reject",
    response_model=ProposedAction,
)
async def reject_action(
    investigation_id: str,
    action_id: str,
    body: ActionRejection,
    engine: AsyncEngine = Depends(get_engine),
) -> ProposedAction:
    repository = InvestigationRepository(engine)
    action = await repository.get_action(investigation_id, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Proposed action not found")
    if action.status != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action.status}")
    return await repository.mark_action_status(
        investigation_id,
        action_id,
        "rejected",
        error=body.reason,
    )


@router.get("/{investigation_id}", response_model=InvestigationView)
async def get_investigation(
    investigation_id: str,
    engine: AsyncEngine = Depends(get_engine),
) -> InvestigationView:
    view = await InvestigationRepository(engine).get(investigation_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return view


@router.get("/{investigation_id}/events")
async def stream_investigation_events(
    investigation_id: str,
    request: Request,
    after: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    engine: AsyncEngine = Depends(get_engine),
) -> StreamingResponse:
    repository = InvestigationRepository(engine)
    view = await repository.get(investigation_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    cursor = after
    if last_event_id and last_event_id.isdigit():
        cursor = max(cursor, int(last_event_id))

    async def event_stream() -> AsyncIterator[str]:
        sequence = cursor
        idle_ticks = 0
        while True:
            if await request.is_disconnected():
                return
            events = await repository.events_after(investigation_id, sequence)
            if events:
                idle_ticks = 0
                for event in events:
                    sequence = event.sequence
                    yield (
                        f"id: {event.sequence}\n"
                        f"event: {event.event_type}\n"
                        f"data: {event.model_dump_json()}\n\n"
                    )
            else:
                idle_ticks += 1
                current = await repository.get(investigation_id)
                if current is None or current.status in {"completed", "failed", "cancelled"}:
                    return
                if idle_ticks >= 40:
                    idle_ticks = 0
                    yield f": keepalive {json.dumps({'investigation_id': investigation_id})}\n\n"
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
