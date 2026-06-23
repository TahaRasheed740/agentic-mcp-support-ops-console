from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.investigations.schemas import (
    Classification,
    Diagnosis,
    EventType,
    EvidenceView,
    InvestigationEventEnvelope,
    InvestigationListItem,
    InvestigationPlan,
    InvestigationView,
    ProposedAction,
    SpecialistReport,
)
from tracedesk_api.models import (
    Investigation,
    InvestigationEvent,
    InvestigationEvidence,
    InvestigationProposedAction,
    InvestigationSpecialistReport,
)


class InvestigationRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create(
        self,
        *,
        case_id: str,
        session_id: str | None,
        persona_id: str,
        router_model: str,
        investigator_model: str,
    ) -> str:
        investigation_id = str(uuid4())
        now = datetime.now(UTC)
        async with self.engine.begin() as connection:
            await connection.execute(
                insert(Investigation).values(
                    id=investigation_id,
                    case_id=case_id,
                    session_id=session_id,
                    persona_id=persona_id,
                    status="queued",
                    router_model=router_model,
                    investigator_model=investigator_model,
                    classification=None,
                    plan=None,
                    diagnosis=None,
                    drafted_response=None,
                    input_tokens=0,
                    output_tokens=0,
                    cache_read_tokens=0,
                    cache_creation_tokens=0,
                    tool_calls=0,
                    error=None,
                    created_at=now,
                    started_at=None,
                    completed_at=None,
                )
            )
        await self.append_event(
            investigation_id,
            "investigation.created",
            "workflow",
            {"case_id": case_id, "status": "queued"},
        )
        return investigation_id

    async def append_event(
        self,
        investigation_id: str,
        event_type: EventType,
        agent: str,
        payload: dict[str, object],
    ) -> InvestigationEventEnvelope:
        now = datetime.now(UTC)
        async with self.engine.begin() as connection:
            await connection.execute(
                select(Investigation.id)
                .where(Investigation.id == investigation_id)
                .with_for_update()
            )
            current = await connection.scalar(
                select(func.max(InvestigationEvent.sequence)).where(
                    InvestigationEvent.investigation_id == investigation_id
                )
            )
            sequence = int(current or 0) + 1
            await connection.execute(
                insert(InvestigationEvent).values(
                    investigation_id=investigation_id,
                    sequence=sequence,
                    occurred_at=now,
                    event_type=event_type,
                    agent=agent,
                    payload=payload,
                )
            )
        return InvestigationEventEnvelope(
            sequence=sequence,
            timestamp=now,
            event_type=event_type,
            agent=agent,
            payload=payload,
        )

    async def mark_started(self, investigation_id: str) -> None:
        now = datetime.now(UTC)
        await self._update(investigation_id, status="running", started_at=now)
        await self.append_event(
            investigation_id,
            "investigation.started",
            "workflow",
            {"status": "running"},
        )

    async def save_classification(
        self, investigation_id: str, classification: Classification
    ) -> None:
        await self._update(
            investigation_id, classification=classification.model_dump(mode="json")
        )
        await self.append_event(
            investigation_id,
            "classification.completed",
            "router",
            classification.model_dump(mode="json"),
        )

    async def save_plan(self, investigation_id: str, plan: InvestigationPlan) -> None:
        await self._update(investigation_id, plan=plan.model_dump(mode="json"))
        await self.append_event(
            investigation_id, "plan.completed", "router", plan.model_dump(mode="json")
        )

    async def save_budget(
        self,
        investigation_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
        tool_calls: int,
    ) -> None:
        await self._update(
            investigation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            tool_calls=tool_calls,
        )
        await self.append_event(
            investigation_id,
            "budget.updated",
            "workflow",
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_creation_tokens": cache_creation_tokens,
                "tool_calls": tool_calls,
            },
        )

    async def add_evidence(
        self,
        investigation_id: str,
        item: dict[str, Any],
    ) -> tuple[EvidenceView, bool]:
        chunk_id = str(item["chunk_id"])
        async with self.engine.begin() as connection:
            existing = (
                await connection.execute(
                    select(InvestigationEvidence).where(
                        InvestigationEvidence.investigation_id == investigation_id,
                        InvestigationEvidence.chunk_id == chunk_id,
                    )
                )
            ).mappings().one_or_none()
            if existing is not None:
                return _evidence_view(existing), False
            count = int(
                await connection.scalar(
                    select(func.count())
                    .select_from(InvestigationEvidence)
                    .where(InvestigationEvidence.investigation_id == investigation_id)
                )
                or 0
            )
            values = {
                "investigation_id": investigation_id,
                "citation_id": f"E{count + 1}",
                "document_id": str(item["document_id"]),
                "chunk_id": chunk_id,
                "title": str(item["title"]),
                "source_path": str(item["source_path"]),
                "excerpt": str(item["content"]),
                "score": float(item["score"]) if item.get("score") is not None else None,
                "created_at": datetime.now(UTC),
            }
            await connection.execute(insert(InvestigationEvidence).values(**values))
        evidence = EvidenceView.model_validate(values)
        await self.append_event(
            investigation_id,
            "evidence.added",
            "investigator",
            evidence.model_dump(mode="json"),
        )
        return evidence, True

    async def save_specialist_report(
        self, investigation_id: str, report: SpecialistReport
    ) -> None:
        values = {
            "investigation_id": investigation_id,
            "specialist": report.specialist,
            "status": report.status,
            "rationale": report.rationale,
            "findings": report.findings,
            "evidence_ids": report.evidence_ids,
            "proposed_actions": report.proposed_actions,
            "created_at": datetime.now(UTC),
        }
        async with self.engine.begin() as connection:
            await connection.execute(insert(InvestigationSpecialistReport).values(**values))
        await self.append_event(
            investigation_id,
            "specialist.completed",
            report.specialist,
            report.model_dump(mode="json"),
        )

    async def create_proposed_action(
        self,
        investigation_id: str,
        *,
        action_id: str,
        action_type: str,
        tool_name: str,
        title: str,
        rationale: str,
        arguments: dict[str, object],
        evidence_ids: list[str],
        idempotency_key: str,
    ) -> ProposedAction:
        values = {
            "id": action_id,
            "investigation_id": investigation_id,
            "action_type": action_type,
            "service": "support",
            "tool_name": tool_name,
            "title": title,
            "rationale": rationale,
            "arguments": arguments,
            "evidence_ids": evidence_ids,
            "status": "pending",
            "idempotency_key": idempotency_key,
            "result": None,
            "error": None,
            "created_at": datetime.now(UTC),
            "decided_at": None,
            "executed_at": None,
        }
        async with self.engine.begin() as connection:
            await connection.execute(insert(InvestigationProposedAction).values(**values))
        action = ProposedAction.model_validate(values)
        await self.append_event(
            investigation_id,
            "action.proposed",
            "workflow",
            action.model_dump(mode="json"),
        )
        return action

    async def get_action(self, investigation_id: str, action_id: str) -> ProposedAction | None:
        async with self.engine.connect() as connection:
            row = (
                await connection.execute(
                    select(InvestigationProposedAction).where(
                        InvestigationProposedAction.investigation_id == investigation_id,
                        InvestigationProposedAction.id == action_id,
                    )
                )
            ).mappings().one_or_none()
        return _action_view(row) if row is not None else None

    async def mark_action_status(
        self,
        investigation_id: str,
        action_id: str,
        status: str,
        *,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> ProposedAction:
        now = datetime.now(UTC)
        values: dict[str, object] = {"status": status}
        if status in {"approved", "rejected", "stale"}:
            values["decided_at"] = now
        if status in {"executed", "failed"}:
            values["executed_at"] = now
        if result is not None:
            values["result"] = result
        if error is not None:
            values["error"] = error[:4000]
        async with self.engine.begin() as connection:
            await connection.execute(
                update(InvestigationProposedAction)
                .where(
                    InvestigationProposedAction.investigation_id == investigation_id,
                    InvestigationProposedAction.id == action_id,
                )
                .values(**values)
            )
            row = (
                await connection.execute(
                    select(InvestigationProposedAction).where(
                        InvestigationProposedAction.investigation_id == investigation_id,
                        InvestigationProposedAction.id == action_id,
                    )
                )
            ).mappings().one()
        action = _action_view(row)
        event_type: EventType = {
            "approved": "action.approved",
            "rejected": "action.rejected",
            "executed": "action.executed",
            "failed": "action.failed",
            "stale": "action.stale",
        }.get(status, "action.approved")  # type: ignore[assignment]
        await self.append_event(
            investigation_id,
            event_type,
            "approval",
            action.model_dump(mode="json"),
        )
        return action

    async def complete(self, investigation_id: str, diagnosis: Diagnosis) -> None:
        now = datetime.now(UTC)
        await self._update(
            investigation_id,
            status="completed",
            diagnosis=diagnosis.model_dump(mode="json"),
            drafted_response=diagnosis.drafted_response,
            completed_at=now,
        )
        await self.append_event(
            investigation_id,
            "diagnosis.completed",
            "investigator",
            diagnosis.model_dump(mode="json"),
        )
        await self.append_event(
            investigation_id,
            "investigation.completed",
            "workflow",
            {"status": "completed"},
        )

    async def fail(self, investigation_id: str, message: str) -> None:
        await self._update(
            investigation_id,
            status="failed",
            error=message[:4000],
            completed_at=datetime.now(UTC),
        )
        await self.append_event(
            investigation_id,
            "investigation.failed",
            "workflow",
            {"status": "failed", "message": message[:1000]},
        )

    async def events_after(
        self, investigation_id: str, sequence: int
    ) -> list[InvestigationEventEnvelope]:
        async with self.engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(InvestigationEvent)
                        .where(
                            InvestigationEvent.investigation_id == investigation_id,
                            InvestigationEvent.sequence > sequence,
                        )
                        .order_by(InvestigationEvent.sequence)
                    )
                )
                .mappings()
                .all()
            )
        return [
            InvestigationEventEnvelope(
                sequence=int(row["sequence"]),
                timestamp=row["occurred_at"],
                event_type=row["event_type"],
                agent=row["agent"],
                payload=row["payload"],
            )
            for row in rows
        ]

    async def get(self, investigation_id: str) -> InvestigationView | None:
        async with self.engine.connect() as connection:
            row = (
                await connection.execute(
                    select(Investigation).where(Investigation.id == investigation_id)
                )
            ).mappings().one_or_none()
            if row is None:
                return None
            evidence_rows = (
                (
                    await connection.execute(
                        select(InvestigationEvidence)
                        .where(InvestigationEvidence.investigation_id == investigation_id)
                        .order_by(InvestigationEvidence.id)
                    )
                )
                .mappings()
                .all()
            )
            specialist_rows = (
                (
                    await connection.execute(
                        select(InvestigationSpecialistReport)
                        .where(
                            InvestigationSpecialistReport.investigation_id
                            == investigation_id
                        )
                        .order_by(InvestigationSpecialistReport.id)
                    )
                )
                .mappings()
                .all()
            )
            action_rows = (
                (
                    await connection.execute(
                        select(InvestigationProposedAction)
                        .where(
                            InvestigationProposedAction.investigation_id
                            == investigation_id
                        )
                        .order_by(InvestigationProposedAction.created_at)
                    )
                )
                .mappings()
                .all()
            )
        return InvestigationView(
            id=row["id"],
            case_id=row["case_id"],
            status=row["status"],
            router_model=row["router_model"],
            investigator_model=row["investigator_model"],
            classification=(
                Classification.model_validate(row["classification"])
                if row["classification"]
                else None
            ),
            plan=InvestigationPlan.model_validate(row["plan"]) if row["plan"] else None,
            diagnosis=Diagnosis.model_validate(row["diagnosis"]) if row["diagnosis"] else None,
            drafted_response=row["drafted_response"],
            specialist_reports=[_specialist_view(item) for item in specialist_rows],
            proposed_actions=[_action_view(item) for item in action_rows],
            evidence=[_evidence_view(item) for item in evidence_rows],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cache_read_tokens=row["cache_read_tokens"],
            cache_creation_tokens=row["cache_creation_tokens"],
            tool_calls=row["tool_calls"],
            error=row["error"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    async def list_recent(self, limit: int = 25) -> list[InvestigationListItem]:
        async with self.engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(
                            Investigation.id,
                            Investigation.case_id,
                            Investigation.status,
                            Investigation.classification,
                            Investigation.diagnosis,
                            Investigation.tool_calls,
                            Investigation.created_at,
                            Investigation.completed_at,
                            func.count(InvestigationEvidence.id).label("evidence_count"),
                        )
                        .outerjoin(
                            InvestigationEvidence,
                            InvestigationEvidence.investigation_id == Investigation.id,
                        )
                        .group_by(Investigation.id)
                        .order_by(Investigation.created_at.desc())
                        .limit(limit)
                    )
                )
                .mappings()
                .all()
            )
            action_counts = (
                (
                    await connection.execute(
                        select(
                            InvestigationProposedAction.investigation_id,
                            func.count(InvestigationProposedAction.id).label("action_count"),
                        ).group_by(InvestigationProposedAction.investigation_id)
                    )
                )
                .mappings()
                .all()
            )
        actions_by_investigation = {
            row["investigation_id"]: int(row["action_count"]) for row in action_counts
        }
        return [
            InvestigationListItem(
                id=row["id"],
                case_id=row["case_id"],
                status=row["status"],
                category=(
                    str(row["classification"].get("category"))
                    if isinstance(row["classification"], dict)
                    else None
                ),
                confidence=(
                    row["diagnosis"].get("confidence")
                    if isinstance(row["diagnosis"], dict)
                    else None
                ),
                summary=(
                    str(row["diagnosis"].get("summary"))
                    if isinstance(row["diagnosis"], dict)
                    else None
                ),
                tool_calls=int(row["tool_calls"]),
                evidence_count=int(row["evidence_count"]),
                proposed_action_count=actions_by_investigation.get(row["id"], 0),
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    async def _update(self, investigation_id: str, **values: object) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(
                update(Investigation).where(Investigation.id == investigation_id).values(**values)
            )


def _evidence_view(row: Any) -> EvidenceView:
    return EvidenceView(
        citation_id=row["citation_id"],
        document_id=row["document_id"],
        chunk_id=row["chunk_id"],
        title=row["title"],
        source_path=row["source_path"],
        excerpt=row["excerpt"],
        score=row["score"],
    )


def _specialist_view(row: Any) -> SpecialistReport:
    return SpecialistReport(
        specialist=row["specialist"],
        status=row["status"],
        rationale=row["rationale"],
        findings=row["findings"],
        evidence_ids=row["evidence_ids"],
        proposed_actions=row["proposed_actions"],
    )


def _action_view(row: Any) -> ProposedAction:
    return ProposedAction(
        id=row["id"],
        action_type=row["action_type"],
        service=row["service"],
        tool_name=row["tool_name"],
        title=row["title"],
        rationale=row["rationale"],
        arguments=row["arguments"],
        evidence_ids=row["evidence_ids"],
        status=row["status"],
        result=row["result"],
        error=row["error"],
        created_at=row["created_at"],
        decided_at=row["decided_at"],
        executed_at=row["executed_at"],
    )
