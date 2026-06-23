from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine
from tracedesk_api.models import (
    BenchmarkCase,
    Investigation,
    InvestigationEvent,
    InvestigationEvidence,
)


async def build_report(ticket_ids: list[str]) -> dict[str, Any]:
    engine = create_engine(get_settings())
    cases: list[dict[str, Any]] = []
    try:
        async with engine.connect() as connection:
            for ticket_id in ticket_ids:
                investigation = (
                    await connection.execute(
                        select(Investigation)
                        .where(Investigation.case_id == ticket_id)
                        .order_by(Investigation.created_at.desc())
                        .limit(1)
                    )
                ).mappings().one_or_none()
                benchmark = (
                    await connection.execute(
                        select(BenchmarkCase).where(BenchmarkCase.ticket_id == ticket_id)
                    )
                ).mappings().one_or_none()
                if investigation is None or benchmark is None:
                    cases.append({"ticket_id": ticket_id, "status": "missing"})
                    continue
                evidence_rows = (
                    (
                        await connection.execute(
                            select(InvestigationEvidence).where(
                                InvestigationEvidence.investigation_id == investigation["id"]
                            )
                        )
                    )
                    .mappings()
                    .all()
                )
                requested_tools = (
                    (
                        await connection.execute(
                            select(InvestigationEvent.payload).where(
                                InvestigationEvent.investigation_id == investigation["id"],
                                InvestigationEvent.event_type == "tool.requested",
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                evidence_ids = {str(row["citation_id"]) for row in evidence_rows}
                document_ids = {str(row["document_id"]) for row in evidence_rows}
                diagnosis = investigation["diagnosis"] or {}
                cited_ids = {
                    str(item["evidence_id"])
                    for item in diagnosis.get("citations", [])
                    if isinstance(item, dict) and "evidence_id" in item
                }
                required_sources = set(benchmark["required_sources"])
                tool_names = [str(payload.get("tool")) for payload in requested_tools]
                cases.append(
                    {
                        "ticket_id": ticket_id,
                        "investigation_id": investigation["id"],
                        "status": investigation["status"],
                        "classification": investigation["classification"],
                        "root_cause": diagnosis.get("root_cause"),
                        "confidence": diagnosis.get("confidence"),
                        "required_sources": sorted(required_sources),
                        "required_sources_found": sorted(required_sources & document_ids),
                        "all_required_sources_found": required_sources <= document_ids,
                        "citation_ids": sorted(cited_ids),
                        "citation_valid": bool(cited_ids) and cited_ids <= evidence_ids,
                        "tool_names": tool_names,
                        "write_tools_used": any(
                            name in {"update_ticket_status", "add_internal_note"}
                            for name in tool_names
                        ),
                        "usage": {
                            "input_tokens": investigation["input_tokens"],
                            "output_tokens": investigation["output_tokens"],
                            "cache_read_tokens": investigation["cache_read_tokens"],
                            "cache_creation_tokens": investigation["cache_creation_tokens"],
                            "tool_calls": investigation["tool_calls"],
                        },
                        "error": investigation["error"],
                    }
                )
    finally:
        await engine.dispose()
    completed = [item for item in cases if item.get("status") == "completed"]
    return {
        "tickets": ticket_ids,
        "completed": len(completed),
        "all_completed": len(completed) == len(ticket_ids),
        "required_source_success_rate": (
            sum(bool(item.get("all_required_sources_found")) for item in cases) / len(cases)
            if cases
            else 0
        ),
        "citation_validity_rate": (
            sum(bool(item.get("citation_valid")) for item in completed) / len(completed)
            if completed
            else 0
        ),
        "unauthorized_write_count": sum(bool(item.get("write_tools_used")) for item in cases),
        "cases": cases,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Report representative live investigation results")
    parser.add_argument("tickets", nargs="*", default=["TKT-1001", "TKT-1007", "TKT-1013"])
    parser.add_argument("--output", type=Path, default=Path("reports/investigations/latest.json"))
    args = parser.parse_args()
    report = await build_report(args.tickets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    if not report["all_completed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
