from typing import Literal

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.dependencies import get_engine
from tracedesk_api.mcp_layer.api_auth import authorization_for_request
from tracedesk_api.mcp_layer.gateway import MCPGateway, MCPGatewayError
from tracedesk_api.schemas import EvidenceItem, KnowledgeSearchResponse

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(min_length=2, max_length=800),
    limit: int = Query(default=8, ge=1, le=20),
    mode: Literal["hybrid", "semantic", "lexical"] = Query(default="hybrid"),
    tracedesk_session: str | None = Cookie(default=None),
    engine: AsyncEngine = Depends(get_engine),
) -> KnowledgeSearchResponse:
    authorization = await authorization_for_request(tracedesk_session, engine)
    try:
        result = await MCPGateway().call_tool(
            "knowledge",
            "search_knowledge",
            {"query": q, "limit": limit, "mode": mode},
            authorization,
        )
    except MCPGatewayError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    items = [EvidenceItem.model_validate(item) for item in result["data"]]
    return KnowledgeSearchResponse(query=q, mode=mode, items=items)
