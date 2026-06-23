from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from tracedesk_api.evaluation import evaluate_benchmarks

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


@router.get("/latest")
async def latest_evaluation() -> dict[str, Any]:
    return evaluate_benchmarks()
