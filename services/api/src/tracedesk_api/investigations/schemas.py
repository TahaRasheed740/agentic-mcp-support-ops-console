from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

InvestigationStatus = Literal["queued", "running", "completed", "failed", "cancelled"]
SpecialistName = Literal["documentation", "account", "reliability"]
ActionStatus = Literal["pending", "approved", "rejected", "executing", "executed", "stale", "failed"]
ActionType = Literal["add_internal_note", "update_ticket_status"]
EventType = Literal[
    "investigation.created",
    "investigation.started",
    "classification.completed",
    "plan.completed",
    "agent.started",
    "tool.requested",
    "tool.completed",
    "evidence.added",
    "model.text_delta",
    "budget.updated",
    "retry.scheduled",
    "specialist.started",
    "specialist.completed",
    "specialist.reconciled",
    "action.proposed",
    "action.approved",
    "action.rejected",
    "action.executed",
    "action.failed",
    "action.stale",
    "diagnosis.completed",
    "investigation.completed",
    "investigation.failed",
]


class Classification(BaseModel):
    category: str = Field(min_length=2, max_length=60)
    urgency: Literal["low", "normal", "high", "urgent"]
    complexity: Literal["simple", "moderate", "complex"]
    summary: str = Field(min_length=10, max_length=500)
    rationale: str = Field(min_length=10, max_length=800)


class InvestigationPlan(BaseModel):
    hypotheses: list[str] = Field(min_length=1, max_length=5)
    evidence_needed: list[str] = Field(min_length=1, max_length=8)
    allowed_tools: list[str] = Field(min_length=1, max_length=10)
    steps: list[str] = Field(min_length=2, max_length=8)


class Citation(BaseModel):
    evidence_id: str = Field(pattern=r"^E[1-9][0-9]*$")
    supports: str = Field(min_length=5, max_length=500)


class Finding(BaseModel):
    claim: str = Field(min_length=5, max_length=800)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class Diagnosis(BaseModel):
    summary: str = Field(min_length=10, max_length=1200)
    root_cause: str = Field(min_length=5, max_length=800)
    confidence: Literal["low", "medium", "high"]
    findings: list[Finding] = Field(min_length=1, max_length=10)
    citations: list[Citation] = Field(min_length=1, max_length=12)
    proposed_actions: list[str] = Field(default_factory=list, max_length=8)
    drafted_response: str = Field(min_length=20, max_length=4000)


class SpecialistReport(BaseModel):
    specialist: SpecialistName
    status: Literal["completed", "skipped", "conflict"]
    rationale: str = Field(min_length=5, max_length=1000)
    findings: list[str] = Field(default_factory=list, max_length=8)
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    proposed_actions: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("rationale", mode="before")
    @classmethod
    def trim_rationale(cls, value: object) -> object:
        return _clip_text(value, 1000)


class ProposedAction(BaseModel):
    id: str
    action_type: ActionType
    service: Literal["support"]
    tool_name: ActionType
    title: str = Field(min_length=5, max_length=240)
    rationale: str = Field(min_length=5, max_length=1200)
    arguments: dict[str, object]
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    status: ActionStatus
    result: dict[str, object] | None
    error: str | None
    created_at: datetime
    decided_at: datetime | None
    executed_at: datetime | None


class EvidenceView(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    title: str
    source_path: str
    excerpt: str
    score: float | None


class InvestigationEventEnvelope(BaseModel):
    sequence: int
    timestamp: datetime
    event_type: EventType
    agent: str
    payload: dict[str, object]


class InvestigationCreate(BaseModel):
    case_id: str = Field(min_length=3, max_length=30)


class InvestigationCreated(BaseModel):
    id: str
    status: InvestigationStatus


class InvestigationListItem(BaseModel):
    id: str
    case_id: str
    status: InvestigationStatus
    category: str | None
    confidence: Literal["low", "medium", "high"] | None
    summary: str | None
    tool_calls: int
    evidence_count: int
    proposed_action_count: int
    created_at: datetime
    completed_at: datetime | None


def _clip_text(value: object, limit: int) -> object:
    if not isinstance(value, str) or len(value) <= limit:
        return value
    suffix = " ... [truncated]"
    return value[: limit - len(suffix)].rstrip() + suffix


class ActionRejection(BaseModel):
    reason: str = Field(default="Rejected by reviewer", min_length=3, max_length=1000)


class InvestigationView(BaseModel):
    id: str
    case_id: str
    status: InvestigationStatus
    router_model: str
    investigator_model: str
    classification: Classification | None
    plan: InvestigationPlan | None
    diagnosis: Diagnosis | None
    drafted_response: str | None
    specialist_reports: list[SpecialistReport]
    proposed_actions: list[ProposedAction]
    evidence: list[EvidenceView]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    tool_calls: int
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
