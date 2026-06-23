from __future__ import annotations

import json
import os
from typing import Literal

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from tracedesk_api.mcp_layer.authorization import require_scope
from tracedesk_api.mcp_layer.contracts import AuthorizationContext, ToolResponse
from tracedesk_api.mcp_layer.runtime import mcp_engine, response
from tracedesk_api.models import KnowledgeChunk, KnowledgeDocument
from tracedesk_api.retrieval import HybridRetriever

knowledge_mcp = FastMCP(
    "TraceDesk Knowledge",
    instructions="Search and inspect versioned Acme Automations support evidence.",
    stateless_http=True,
    json_response=True,
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)


@knowledge_mcp.tool()
async def search_knowledge(
    query: str,
    authorization: AuthorizationContext,
    limit: int = 8,
    mode: Literal["hybrid", "semantic", "lexical"] = "hybrid",
) -> ToolResponse:
    """Search support evidence and expose semantic, lexical, and fused ranks."""
    require_scope(authorization, "knowledge:read")
    if not 2 <= len(query) <= 800:
        raise ValueError("query must contain between 2 and 800 characters")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    items = await HybridRetriever(mcp_engine()).search(query, limit=limit, mode=mode)
    return response(
        "knowledge",
        authorization,
        [item.model_dump(mode="json") for item in items],
    )


@knowledge_mcp.tool()
async def get_document(
    document_id: str,
    authorization: AuthorizationContext,
) -> ToolResponse:
    """Read a source and all of its chunks by stable document identifier."""
    require_scope(authorization, "knowledge:read")
    async with mcp_engine().connect() as connection:
        document = (
            await connection.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
        ).mappings().one_or_none()
        if document is None:
            raise ValueError(f"Knowledge document not found: {document_id}")
        chunks = (
            (
                await connection.execute(
                    select(KnowledgeChunk)
                    .where(KnowledgeChunk.document_id == document_id)
                    .order_by(KnowledgeChunk.chunk_index)
                )
            )
            .mappings()
            .all()
        )
    data = {key: value for key, value in document.items() if key != "checksum"}
    data["chunks"] = [
        {
            "id": chunk["id"],
            "heading": chunk["heading"],
            "content": chunk["content"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]
    return response("knowledge", authorization, data)


@knowledge_mcp.resource("acme://knowledge/catalog")
async def knowledge_catalog() -> str:
    """Current and superseded support source catalog."""
    async with mcp_engine().connect() as connection:
        rows = (
            (
                await connection.execute(
                    select(
                        KnowledgeDocument.id,
                        KnowledgeDocument.title,
                        KnowledgeDocument.product_area,
                        KnowledgeDocument.version,
                        KnowledgeDocument.status,
                        KnowledgeDocument.source_type,
                    ).order_by(KnowledgeDocument.product_area, KnowledgeDocument.title)
                )
            )
            .mappings()
            .all()
        )
    return json.dumps([dict(row) for row in rows], default=str)


@knowledge_mcp.prompt()
def evidence_search_plan(customer_symptom: str) -> str:
    """Create a disciplined evidence-search plan for a support symptom."""
    return (
        "Investigate the customer symptom using current Acme Automations evidence. "
        "Search for the exact symptom, collect the smallest relevant source set, "
        "identify superseded guidance, and separate observed facts from hypotheses.\n\n"
        f"Customer symptom: {customer_symptom}"
    )
