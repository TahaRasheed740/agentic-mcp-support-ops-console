from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.dependencies import get_engine
from tracedesk_api.mcp_layer.api_auth import authorization_for_request
from tracedesk_api.mcp_layer.contracts import (
    ExplorerCallResponse,
    ExplorerCatalog,
    ServiceName,
    ToolCallRequest,
)
from tracedesk_api.mcp_layer.gateway import MCPGateway, MCPGatewayError

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP explorer"])


@router.get("/servers", response_model=ExplorerCatalog)
async def list_servers() -> ExplorerCatalog:
    try:
        return await MCPGateway().catalog()
    except MCPGatewayError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/{service}/tools/{tool}", response_model=ExplorerCallResponse)
async def call_tool(
    service: ServiceName,
    tool: str,
    request: ToolCallRequest,
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> ExplorerCallResponse:
    authorization = await authorization_for_request(tracedesk_session, engine)
    try:
        result = await MCPGateway().call_tool(service, tool, request.arguments, authorization)
    except MCPGatewayError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ExplorerCallResponse(server=service, tool=tool, result=result)
