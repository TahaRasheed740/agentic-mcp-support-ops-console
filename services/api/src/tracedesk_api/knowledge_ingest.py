from __future__ import annotations

import argparse
import asyncio
import json

from sqlalchemy import delete, func, insert, select

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine
from tracedesk_api.embeddings import get_embedding_service
from tracedesk_api.knowledge_sources import chunk_document, load_benchmarks, load_sources
from tracedesk_api.models import BenchmarkCase, KnowledgeChunk, KnowledgeDocument


async def ingest_knowledge(*, force: bool = False) -> tuple[bool, dict[str, int]]:
    settings = get_settings()
    sources = load_sources(settings.knowledge_dir, settings.pdf_dir)
    chunks = [chunk for source in sources for chunk in chunk_document(source)]
    version, benchmark_cases = load_benchmarks(settings.knowledge_dir / "benchmarks" / "v1.yaml")
    engine = create_engine(settings)
    try:
        async with engine.connect() as connection:
            existing = int(
                await connection.scalar(select(func.count()).select_from(KnowledgeDocument)) or 0
            )
        if existing and not force:
            return False, {
                "documents": existing,
                "chunks": len(chunks),
                "benchmarks": len(benchmark_cases),
            }

        embedding_service = get_embedding_service()
        embeddings = await asyncio.to_thread(
            embedding_service.embed_documents, [chunk.content for chunk in chunks]
        )
        async with engine.begin() as connection:
            if force:
                await connection.execute(delete(BenchmarkCase))
                await connection.execute(delete(KnowledgeChunk))
                await connection.execute(delete(KnowledgeDocument))
            await connection.execute(
                insert(KnowledgeDocument),
                [
                    {
                        "id": source.id,
                        "title": source.title,
                        "product_area": source.product_area,
                        "version": source.version,
                        "status": source.status,
                        "source_type": source.source_type,
                        "source_path": source.source_path,
                        "published_at": source.published_at,
                        "superseded_by": source.superseded_by,
                        "checksum": source.checksum,
                    }
                    for source in sources
                ],
            )
            await connection.execute(
                insert(KnowledgeChunk),
                [
                    {
                        "id": chunk.id,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "heading": chunk.heading,
                        "content": chunk.content,
                        "token_count": chunk.token_count,
                        "embedding": embedding,
                    }
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ],
            )
            await connection.execute(
                insert(BenchmarkCase),
                [
                    {
                        "ticket_id": item["ticket_id"],
                        "dataset_version": version,
                        "expected_category": item["expected_category"],
                        "acceptable_root_causes": item["acceptable_root_causes"],
                        "required_sources": item["required_sources"],
                        "prohibited_claims": item["prohibited_claims"],
                        "allowed_tools": item["allowed_tools"],
                        "expected_actions": item["expected_actions"],
                        "escalation_required": item["escalation_required"],
                    }
                    for item in benchmark_cases
                ],
            )
        return True, {
            "documents": len(sources),
            "chunks": len(chunks),
            "benchmarks": len(benchmark_cases),
        }
    finally:
        await engine.dispose()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest the TraceDesk knowledge corpus.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    changed, counts = await ingest_knowledge(force=args.force)
    result = {"ingested": changed, "counts": counts}
    print(json.dumps(result, sort_keys=True) if args.json else result)


if __name__ == "__main__":
    asyncio.run(_main())
