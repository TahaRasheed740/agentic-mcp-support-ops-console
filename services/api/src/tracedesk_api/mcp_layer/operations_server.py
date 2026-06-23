from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, or_, select

from tracedesk_api.mcp_layer.authorization import require_scope
from tracedesk_api.mcp_layer.contracts import AuthorizationContext, ToolResponse
from tracedesk_api.mcp_layer.runtime import mcp_engine, response
from tracedesk_api.models import Incident, Integration, JobRun, LogEntry, Organization

operations_mcp = FastMCP(
    "TraceDesk Operations",
    instructions="Read simulated Acme Automations integrations, runs, logs, and incidents.",
    stateless_http=True,
    json_response=True,
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)


@operations_mcp.tool()
async def get_integration(
    integration_id: str,
    authorization: AuthorizationContext,
) -> ToolResponse:
    """Read integration health and organization routing context."""
    require_scope(authorization, "operations:read")
    async with mcp_engine().connect() as connection:
        row = (
            await connection.execute(
                select(
                    Integration.id,
                    Integration.organization_id,
                    Integration.name,
                    Integration.kind,
                    Integration.status,
                    Integration.environment,
                    Integration.last_seen_at,
                    Organization.region,
                )
                .join(Organization, Integration.organization_id == Organization.id)
                .where(Integration.id == integration_id)
            )
        ).mappings().one_or_none()
    if row is None:
        raise ValueError(f"Integration not found: {integration_id}")
    return response("operations", authorization, dict(row))


@operations_mcp.tool()
async def list_recent_runs(
    integration_id: str,
    authorization: AuthorizationContext,
    limit: int = 10,
) -> ToolResponse:
    """List recent job runs for one integration without exposing payload contents."""
    require_scope(authorization, "operations:read")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    async with mcp_engine().connect() as connection:
        rows = (
            (
                await connection.execute(
                    select(JobRun)
                    .where(JobRun.integration_id == integration_id)
                    .order_by(JobRun.started_at.desc())
                    .limit(limit)
                )
            )
            .mappings()
            .all()
        )
    return response("operations", authorization, [dict(row) for row in rows])


@operations_mcp.tool()
async def get_run_logs(
    run_id: str,
    authorization: AuthorizationContext,
    limit: int = 50,
) -> ToolResponse:
    """Read bounded, synthetic logs for a job run."""
    require_scope(authorization, "operations:read")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    async with mcp_engine().connect() as connection:
        rows = (
            (
                await connection.execute(
                    select(LogEntry)
                    .where(LogEntry.job_run_id == run_id)
                    .order_by(LogEntry.occurred_at)
                    .limit(limit)
                )
            )
            .mappings()
            .all()
        )
    return response("operations", authorization, [dict(row) for row in rows])


@operations_mcp.tool()
async def list_incidents(
    region: str,
    authorization: AuthorizationContext,
    limit: int = 10,
) -> ToolResponse:
    """List global and region-specific incidents for correlation."""
    require_scope(authorization, "operations:read")
    if not 1 <= limit <= 25:
        raise ValueError("limit must be between 1 and 25")
    async with mcp_engine().connect() as connection:
        rows = (
            (
                await connection.execute(
                    select(Incident)
                    .where(or_(Incident.region == region, Incident.region == "global"))
                    .order_by(Incident.started_at.desc())
                    .limit(limit)
                )
            )
            .mappings()
            .all()
        )
    return response("operations", authorization, [dict(row) for row in rows])


@operations_mcp.resource("acme://operations/status")
async def operations_status() -> str:
    """Aggregate status of the simulated operations environment."""
    async with mcp_engine().connect() as connection:
        counts = {
            "integrations": int(await connection.scalar(select(func.count()).select_from(Integration)) or 0),
            "runs": int(await connection.scalar(select(func.count()).select_from(JobRun)) or 0),
            "incidents": int(await connection.scalar(select(func.count()).select_from(Incident)) or 0),
        }
    return json.dumps(counts)


@operations_mcp.prompt()
def reliability_investigation(region: str, symptom: str) -> str:
    """Plan a read-only reliability investigation."""
    return (
        f"Investigate {symptom!r} in {region}. Compare queue and execution timing, "
        "correlate global and regional incidents, preserve run IDs, and do not retry "
        "or mutate an integration without explicit approval."
    )
