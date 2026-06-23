from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import String, and_, case, cast, func, literal, or_, select
from sqlalchemy.dialects.postgresql import insert

from tracedesk_api.mcp_layer.authorization import require_approval, require_scope
from tracedesk_api.mcp_layer.contracts import AuthorizationContext, ToolResponse
from tracedesk_api.mcp_layer.runtime import mcp_engine, response
from tracedesk_api.models import (
    DemoSession,
    Integration,
    Organization,
    Plan,
    Ticket,
    TicketOverlay,
    ToolInvocation,
    User,
)

support_mcp = FastMCP(
    "TraceDesk Support",
    instructions="Read support cases and perform only explicitly approved session-overlay writes.",
    stateless_http=True,
    json_response=True,
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)


@support_mcp.tool()
async def list_cases(
    authorization: AuthorizationContext,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> ToolResponse:
    """List support cases using the caller's isolated session overlay."""
    require_scope(authorization, "support:read")
    if page < 1 or not 1 <= page_size <= 75:
        raise ValueError("page and page_size are outside the supported range")
    query, effective_status = _case_query(authorization.session_id)
    if status:
        query = query.where(effective_status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if search:
        pattern = f"%{search[:120]}%"
        query = query.where(
            or_(
                Ticket.subject.ilike(pattern),
                Ticket.description.ilike(pattern),
                Organization.name.ilike(pattern),
                cast(Ticket.id, String).ilike(pattern),
            )
        )
    priority_order = case(
        (Ticket.priority == "urgent", 0),
        (Ticket.priority == "high", 1),
        (Ticket.priority == "normal", 2),
        else_=3,
    )
    paged = query.order_by(priority_order, Ticket.updated_at.desc()).limit(page_size).offset((page - 1) * page_size)
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    status_query, effective_status_for_counts = _case_query(authorization.session_id)
    grouped_status_query = status_query.with_only_columns(
            effective_status_for_counts.label("status"),
            func.count().label("count"),
        ).order_by(None).group_by(effective_status_for_counts)
    async with mcp_engine().connect() as connection:
        rows = (await connection.execute(paged)).mappings().all()
        total = int(await connection.scalar(count_query) or 0)
        status_rows = (await connection.execute(grouped_status_query)).mappings().all()
    data = {
        "items": [_case_item(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "status_counts": {str(row["status"]): int(row["count"]) for row in status_rows},
    }
    return response("support", authorization, data)


@support_mcp.tool()
async def get_case(case_id: str, authorization: AuthorizationContext) -> ToolResponse:
    """Read one support case, requester, organization, and effective overlay state."""
    require_scope(authorization, "support:read")
    query, _ = _case_query(authorization.session_id)
    async with mcp_engine().connect() as connection:
        row = (await connection.execute(query.where(Ticket.id == case_id))).mappings().one_or_none()
        if row is None:
            raise ValueError(f"Support case not found: {case_id}")
        requester = (
            await connection.execute(
                select(User.id, User.name, User.email, User.role).where(User.id == row["requester_id"])
            )
        ).mappings().one()
        member_count = int(
            await connection.scalar(
                select(func.count()).select_from(User).where(User.organization_id == row["org_id"])
            )
            or 0
        )
        open_count = int(
            await connection.scalar(
                select(func.count()).select_from(Ticket).where(
                    Ticket.organization_id == row["org_id"],
                    Ticket.status.in_(("open", "pending", "investigating")),
                )
            )
            or 0
        )
    data = _case_item(row)
    data.update(
        {
            "requester": dict(requester),
            "organization_members": member_count,
            "organization_open_cases": open_count,
        }
    )
    return response("support", authorization, data)


@support_mcp.tool()
async def update_ticket_status(
    case_id: str,
    status: str,
    approval_id: str,
    idempotency_key: str,
    authorization: AuthorizationContext,
) -> ToolResponse:
    """Update a session-overlay ticket status after explicit human approval."""
    require_scope(authorization, "support:write")
    require_approval(authorization, approval_id)
    if status not in {"open", "pending", "investigating", "resolved"}:
        raise ValueError("Unsupported ticket status")
    payload = {"case_id": case_id, "status": status, "approval_id": approval_id}
    return await _write_overlay("update_ticket_status", idempotency_key, payload, authorization)


@support_mcp.tool()
async def add_internal_note(
    case_id: str,
    note: str,
    approval_id: str,
    idempotency_key: str,
    authorization: AuthorizationContext,
) -> ToolResponse:
    """Add a session-overlay internal note after explicit human approval."""
    require_scope(authorization, "support:write")
    require_approval(authorization, approval_id)
    cleaned_note = note.strip()
    if not 3 <= len(cleaned_note) <= 2000:
        raise ValueError("note must contain between 3 and 2000 characters")
    payload = {"case_id": case_id, "note": cleaned_note, "approval_id": approval_id}
    return await _write_overlay("add_internal_note", idempotency_key, payload, authorization)


@support_mcp.resource("acme://support/queue-summary")
async def queue_summary() -> str:
    """Canonical support queue counts by status and priority."""
    async with mcp_engine().connect() as connection:
        status_rows = (
            await connection.execute(select(Ticket.status, func.count()).group_by(Ticket.status))
        ).all()
        priority_rows = (
            await connection.execute(select(Ticket.priority, func.count()).group_by(Ticket.priority))
        ).all()
    return json.dumps(
        {
            "by_status": {str(key): int(value) for key, value in status_rows},
            "by_priority": {str(key): int(value) for key, value in priority_rows},
        }
    )


@support_mcp.prompt()
def case_triage(case_id: str, customer_message: str) -> str:
    """Create a read-first support case triage plan."""
    return (
        f"Triage {case_id}: {customer_message}\n"
        "Read the case and relevant operational context, search current evidence, "
        "state uncertainty, and propose rather than execute any state-changing action."
    )


def _case_query(session_id: str | None) -> tuple[Any, Any]:
    effective_status = func.coalesce(TicketOverlay.status, Ticket.status)
    overlay_condition = and_(
        TicketOverlay.ticket_id == Ticket.id,
        TicketOverlay.session_id == (session_id if session_id else literal("__no_session__")),
    )
    source = (
        Ticket.__table__.join(Organization, Ticket.organization_id == Organization.id)
        .join(Plan, Organization.plan_id == Plan.id)
        .outerjoin(Integration, Ticket.integration_id == Integration.id)
        .outerjoin(TicketOverlay, overlay_condition)
    )
    return (
        select(
            Ticket.id,
            Ticket.subject,
            Ticket.description,
            effective_status.label("effective_status"),
            Ticket.priority,
            Ticket.category,
            Ticket.created_at,
            Ticket.updated_at,
            Ticket.requester_id,
            Organization.id.label("org_id"),
            Organization.name.label("org_name"),
            Organization.region.label("org_region"),
            Organization.status.label("org_status"),
            Plan.name.label("plan_name"),
            Integration.id.label("integration_id"),
            Integration.name.label("integration_name"),
            Integration.kind.label("integration_kind"),
            Integration.status.label("integration_status"),
            Integration.environment.label("integration_environment"),
            Integration.last_seen_at.label("integration_last_seen_at"),
        ).select_from(source),
        effective_status,
    )


def _case_item(row: Any) -> dict[str, Any]:
    integration = None
    if row["integration_id"] is not None:
        integration = {
            "id": row["integration_id"],
            "name": row["integration_name"],
            "kind": row["integration_kind"],
            "status": row["integration_status"],
            "environment": row["integration_environment"],
            "last_seen_at": row["integration_last_seen_at"],
        }
    return {
        "id": row["id"],
        "subject": row["subject"],
        "description": row["description"],
        "status": row["effective_status"],
        "priority": row["priority"],
        "category": row["category"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "requester_id": row["requester_id"],
        "organization": {
            "id": row["org_id"],
            "name": row["org_name"],
            "plan": row["plan_name"],
            "region": row["org_region"],
            "status": row["org_status"],
        },
        "integration": integration,
    }


async def _write_overlay(
    tool_name: str,
    idempotency_key: str,
    payload: dict[str, str],
    authorization: AuthorizationContext,
) -> ToolResponse:
    if not 8 <= len(idempotency_key) <= 100:
        raise ValueError("idempotency_key must contain between 8 and 100 characters")
    assert authorization.session_id is not None
    encoded = json.dumps(payload, sort_keys=True).encode()
    request_hash = hashlib.sha256(encoded).hexdigest()
    async with mcp_engine().begin() as connection:
        prior = (
            await connection.execute(
                select(ToolInvocation).where(
                    ToolInvocation.service == "support",
                    ToolInvocation.tool_name == tool_name,
                    ToolInvocation.idempotency_key == idempotency_key,
                )
            )
        ).mappings().one_or_none()
        if prior is not None:
            if prior["request_hash"] != request_hash:
                raise ValueError("idempotency_key was already used with different arguments")
            return response("support", authorization, prior["response"], idempotent_replay=True)

        session_exists = await connection.scalar(
            select(func.count()).select_from(DemoSession).where(DemoSession.id == authorization.session_id)
        )
        ticket_exists = await connection.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.id == payload["case_id"])
        )
        if not session_exists or not ticket_exists:
            raise ValueError("The demo session or support case does not exist")

        values: dict[str, object] = {
            "session_id": authorization.session_id,
            "ticket_id": payload["case_id"],
            "assigned_persona_id": authorization.persona_id,
            "updated_at": datetime.now(UTC),
        }
        update_values: dict[str, object] = {
            "assigned_persona_id": authorization.persona_id,
            "updated_at": datetime.now(UTC),
        }
        if tool_name == "update_ticket_status":
            values["status"] = payload["status"]
            update_values["status"] = payload["status"]
        else:
            values["internal_note"] = payload["note"]
            update_values["internal_note"] = payload["note"]
        statement = insert(TicketOverlay).values(**values)
        await connection.execute(
            statement.on_conflict_do_update(
                index_elements=[TicketOverlay.session_id, TicketOverlay.ticket_id],
                set_=update_values,
            )
        )
        result: dict[str, object] = {
            "case_id": payload["case_id"],
            "operation": tool_name,
            "session_id": authorization.session_id,
            "approval_id": payload["approval_id"],
        }
        if "status" in payload:
            result["status"] = payload["status"]
        if "note" in payload:
            result["note"] = payload["note"]
        await connection.execute(
            insert(ToolInvocation).values(
                service="support",
                tool_name=tool_name,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                session_id=authorization.session_id,
                response=result,
                created_at=datetime.now(UTC),
            )
        )
    return response("support", authorization, result)
