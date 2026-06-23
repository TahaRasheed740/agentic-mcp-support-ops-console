from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.embeddings import LocalEmbeddingService, get_embedding_service
from tracedesk_api.models import KnowledgeChunk, KnowledgeDocument
from tracedesk_api.schemas import EvidenceItem

RetrievalMode = Literal["hybrid", "semantic", "lexical"]


@dataclass
class RankedCandidate:
    row: dict[str, Any]
    semantic_rank: int | None = None
    lexical_rank: int | None = None
    score: float = 0.0


class HybridRetriever:
    def __init__(
        self,
        engine: AsyncEngine,
        embedding_service: LocalEmbeddingService | None = None,
        rrf_constant: int = 60,
    ) -> None:
        self.engine = engine
        self.embedding_service = embedding_service or get_embedding_service()
        self.rrf_constant = rrf_constant

    async def search(
        self, query: str, *, limit: int = 8, mode: RetrievalMode = "hybrid"
    ) -> list[EvidenceItem]:
        if not query.strip():
            return []
        pool_size = max(24, limit * 4)
        semantic_rows: Sequence[Any] = ()
        all_rows: Sequence[Any] = ()
        if mode in {"hybrid", "semantic"}:
            query_vector = await asyncio.to_thread(self.embedding_service.embed_query, query)
            distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
            semantic_query = (
                _chunk_query()
                .add_columns(distance.label("distance"))
                .order_by(distance)
                .limit(pool_size)
            )
            async with self.engine.connect() as connection:
                semantic_rows = (await connection.execute(semantic_query)).mappings().all()
        if mode in {"hybrid", "lexical"}:
            async with self.engine.connect() as connection:
                all_rows = (await connection.execute(_chunk_query())).mappings().all()

        candidates: dict[str, RankedCandidate] = {}
        for rank, row in enumerate(semantic_rows, start=1):
            candidate = RankedCandidate(row=dict(row), semantic_rank=rank)
            candidate.score += 1 / (self.rrf_constant + rank)
            candidates[str(row["chunk_id"])] = candidate

        if all_rows:
            corpus = [_tokenize(str(row["content"])) for row in all_rows]
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(_tokenize(query))
            ranked_indexes = sorted(
                range(len(scores)), key=lambda index: scores[index], reverse=True
            )
            for rank, index in enumerate(ranked_indexes[:pool_size], start=1):
                if scores[index] <= 0:
                    continue
                row = all_rows[index]
                chunk_id = str(row["chunk_id"])
                candidate = candidates.setdefault(chunk_id, RankedCandidate(row=dict(row)))
                candidate.lexical_rank = rank
                candidate.score += 1 / (self.rrf_constant + rank)

        for candidate in candidates.values():
            if candidate.row["document_status"] == "superseded":
                candidate.score *= 0.72
        ranked = sorted(
            candidates.values(),
            key=lambda candidate: (
                candidate.score,
                candidate.row["document_status"] == "current",
            ),
            reverse=True,
        )[:limit]
        return [_evidence(candidate) for candidate in ranked]


def _chunk_query() -> Any:
    return (
        select(
            KnowledgeChunk.id.label("chunk_id"),
            KnowledgeChunk.document_id,
            KnowledgeChunk.heading,
            KnowledgeChunk.content,
            KnowledgeDocument.title,
            KnowledgeDocument.product_area,
            KnowledgeDocument.version,
            KnowledgeDocument.status.label("document_status"),
            KnowledgeDocument.source_type,
            KnowledgeDocument.source_path,
        )
        .select_from(KnowledgeChunk)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
    )


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _evidence(candidate: RankedCandidate) -> EvidenceItem:
    row = candidate.row
    return EvidenceItem(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        title=row["title"],
        heading=row["heading"],
        product_area=row["product_area"],
        version=row["version"],
        status=row["document_status"],
        source_type=row["source_type"],
        source_path=row["source_path"],
        content=row["content"],
        score=round(candidate.score, 8),
        semantic_rank=candidate.semantic_rank,
        lexical_rank=candidate.lexical_rank,
    )
