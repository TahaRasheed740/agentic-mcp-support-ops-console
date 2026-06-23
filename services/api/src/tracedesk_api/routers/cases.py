from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.dependencies import get_engine
from tracedesk_api.mcp_layer.api_auth import authorization_for_request
from tracedesk_api.mcp_layer.gateway import MCPGateway, MCPGatewayError
from tracedesk_api.models import (
    BenchmarkCase,
    Incident,
    Integration,
    JobRun,
    KnowledgeChunk,
    KnowledgeDocument,
    LogEntry,
    Organization,
    Plan,
    SupportPersona,
    Ticket,
    User,
)
from tracedesk_api.schemas import CaseDetail, CaseListResponse, DomainSummary

router = APIRouter(prefix="/api/v1", tags=["support cases"])


@router.get("/domain/summary", response_model=DomainSummary)
async def domain_summary(engine: AsyncEngine = Depends(get_engine)) -> DomainSummary:
    models = (
        Plan,
        Organization,
        User,
        Integration,
        JobRun,
        LogEntry,
        Ticket,
        Incident,
        SupportPersona,
        KnowledgeDocument,
        KnowledgeChunk,
        BenchmarkCase,
    )
    async with engine.connect() as connection:
        counts = [
            int(await connection.scalar(select(func.count()).select_from(model)) or 0)
            for model in models
        ]
    return DomainSummary(**dict(zip(DomainSummary.model_fields, counts, strict=True)))


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=75),
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> CaseListResponse:
    authorization = await authorization_for_request(tracedesk_session, engine)
    result = await _call(
        "support",
        "list_cases",
        {
            "status": status_filter,
            "priority": priority,
            "search": search,
            "page": page,
            "page_size": page_size,
        },
        authorization,
    )
    return CaseListResponse.model_validate(result["data"])


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str,
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> CaseDetail:
    authorization = await authorization_for_request(tracedesk_session, engine)
    case_result = await _call("support", "get_case", {"case_id": case_id}, authorization)
    data = dict(case_result["data"])
    integration = data.get("integration")
    region = str(data["organization"]["region"])
    incident_call = _call(
        "operations", "list_incidents", {"region": region, "limit": 3}, authorization
    )
    if integration:
        run_call = _call(
            "operations",
            "list_recent_runs",
            {"integration_id": integration["id"], "limit": 10},
            authorization,
        )
        run_result, incident_result = await asyncio.gather(run_call, incident_call)
        data["recent_runs"] = run_result["data"]
    else:
        incident_result = await incident_call
        data["recent_runs"] = []
    data["related_incidents"] = incident_result["data"]
    return CaseDetail.model_validate(data)


async def _call(
    service: Any,
    tool: str,
    arguments: dict[str, Any],
    authorization: Any,
) -> dict[str, Any]:
    try:
        return await MCPGateway().call_tool(service, tool, arguments, authorization)
    except MCPGatewayError as error:
        status_code = 404 if "not found" in str(error).lower() else 502
        raise HTTPException(status_code=status_code, detail=str(error)) from error
