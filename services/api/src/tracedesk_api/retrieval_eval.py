from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine
from tracedesk_api.models import BenchmarkCase, Ticket
from tracedesk_api.retrieval import HybridRetriever, RetrievalMode


async def evaluate_retrieval(*, mode: RetrievalMode = "hybrid", limit: int = 8) -> dict[str, Any]:
    settings = get_settings()
    engine = create_engine(settings)
    try:
        async with engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(
                            BenchmarkCase.ticket_id,
                            BenchmarkCase.dataset_version,
                            BenchmarkCase.required_sources,
                            Ticket.subject,
                            Ticket.description,
                        )
                        .join(Ticket, BenchmarkCase.ticket_id == Ticket.id)
                        .order_by(BenchmarkCase.ticket_id)
                    )
                )
                .mappings()
                .all()
            )
        retriever = HybridRetriever(engine)
        results: list[dict[str, Any]] = []
        required_total = 0
        required_found = 0
        for row in rows:
            query = f"{row['subject']}\n{row['description']}"
            evidence = await retriever.search(query, limit=limit, mode=mode)
            retrieved_sources = [item.document_id for item in evidence]
            required_sources = list(row["required_sources"])
            found_sources = [source for source in required_sources if source in retrieved_sources]
            required_total += len(required_sources)
            required_found += len(found_sources)
            results.append(
                {
                    "ticket_id": row["ticket_id"],
                    "required_sources": required_sources,
                    "found_sources": found_sources,
                    "all_required_found": len(found_sources) == len(required_sources),
                    "retrieved_sources": retrieved_sources,
                }
            )
        case_successes = sum(result["all_required_found"] for result in results)
        report = {
            "dataset_version": rows[0]["dataset_version"] if rows else "unknown",
            "generated_at": datetime.now(UTC).isoformat(),
            "mode": mode,
            "limit": limit,
            "cases": len(results),
            "case_success_rate": case_successes / len(results) if results else 0,
            "required_source_recall": required_found / required_total if required_total else 0,
            "results": results,
        }
        return report
    finally:
        await engine.dispose()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate TraceDesk retrieval against v1 cases.")
    parser.add_argument("--mode", choices=("hybrid", "semantic", "lexical"), default="hybrid")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    report = await evaluate_retrieval(mode=args.mode, limit=args.limit)
    output = args.output or get_settings().retrieval_report_dir / "latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "case_success_rate": report["case_success_rate"],
                "required_source_recall": report["required_source_recall"],
                "report": str(output),
            }
        )
    )
    if report["case_success_rate"] < 0.9:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_main())
