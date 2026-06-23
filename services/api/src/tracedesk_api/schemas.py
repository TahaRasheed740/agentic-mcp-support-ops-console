from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LiveHealth(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "api"


class ReadyHealth(BaseModel):
    status: Literal["ready", "not_ready"]
    service: str = "api"
    database: Literal["connected", "unavailable"]


class Persona(BaseModel):
    id: str
    name: str
    role: str
    initials: str
    specialty: str


class SessionCreate(BaseModel):
    persona_id: str


class DemoSessionView(BaseModel):
    id: str
    persona: Persona
    created_at: datetime
    reset_at: datetime | None


class OrganizationSummary(BaseModel):
    id: str
    name: str
    plan: str
    region: str
    status: str


class IntegrationSummary(BaseModel):
    id: str
    name: str
    kind: str
    status: str
    environment: str
    last_seen_at: datetime


class RequesterSummary(BaseModel):
    id: str
    name: str
    email: str
    role: str


class CaseListItem(BaseModel):
    id: str
    subject: str
    description: str
    status: str
    priority: str
    category: str
    created_at: datetime
    updated_at: datetime
    organization: OrganizationSummary
    integration: IntegrationSummary | None


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    total: int
    page: int
    page_size: int
    status_counts: dict[str, int]


class JobRunSummary(BaseModel):
    id: str
    status: str
    started_at: datetime
    duration_ms: int
    error_code: str | None
    records_processed: int


class IncidentSummary(BaseModel):
    id: str
    title: str
    status: str
    severity: str
    region: str
    started_at: datetime


class CaseDetail(CaseListItem):
    requester: RequesterSummary
    recent_runs: list[JobRunSummary]
    related_incidents: list[IncidentSummary]
    organization_members: int
    organization_open_cases: int


class DomainSummary(BaseModel):
    plans: int
    organizations: int
    users: int
    integrations: int
    job_runs: int
    log_entries: int
    tickets: int
    incidents: int
    personas: int
    knowledge_documents: int
    knowledge_chunks: int
    benchmark_cases: int


class EvidenceItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    heading: str
    product_area: str
    version: str
    status: str
    source_type: str
    source_path: str
    content: str
    score: float
    semantic_rank: int | None
    lexical_rank: int | None


class KnowledgeSearchResponse(BaseModel):
    query: str
    mode: Literal["hybrid", "semantic", "lexical"]
    items: list[EvidenceItem]
