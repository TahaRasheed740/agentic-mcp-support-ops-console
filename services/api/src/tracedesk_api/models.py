from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AppMetadata(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    monthly_run_limit: Mapped[int] = mapped_column(Integer)
    retention_days: Mapped[int] = mapped_column(Integer)
    support_tier: Mapped[str] = mapped_column(String(30))


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"))
    region: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True)
    role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    environment: Mapped[str] = mapped_column(String(30))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    region: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str] = mapped_column(Text)


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(60))
    records_processed: Mapped[int] = mapped_column(Integer)


class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    job_run_id: Mapped[str] = mapped_column(ForeignKey("job_runs.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    level: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    integration_id: Mapped[str | None] = mapped_column(ForeignKey("integrations.id"))
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SupportPersona(Base):
    __tablename__ = "support_personas"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(80))
    initials: Mapped[str] = mapped_column(String(4))
    specialty: Mapped[str] = mapped_column(String(120))


class DemoSession(Base):
    __tablename__ = "demo_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    persona_id: Mapped[str] = mapped_column(ForeignKey("support_personas.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TicketOverlay(Base):
    __tablename__ = "ticket_overlays"
    __table_args__ = (UniqueConstraint("session_id", "ticket_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id", ondelete="CASCADE"))
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"))
    status: Mapped[str | None] = mapped_column(String(30))
    assigned_persona_id: Mapped[str | None] = mapped_column(ForeignKey("support_personas.id"))
    internal_note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"
    __table_args__ = (UniqueConstraint("service", "tool_name", "idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(String(30))
    tool_name: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id", ondelete="CASCADE"))
    response: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("demo_sessions.id", ondelete="SET NULL"), index=True
    )
    persona_id: Mapped[str] = mapped_column(ForeignKey("support_personas.id"))
    status: Mapped[str] = mapped_column(String(30), index=True)
    router_model: Mapped[str] = mapped_column(String(100))
    investigator_model: Mapped[str] = mapped_column(String(100))
    classification: Mapped[dict[str, object] | None] = mapped_column(JSON)
    plan: Mapped[dict[str, object] | None] = mapped_column(JSON)
    diagnosis: Mapped[dict[str, object] | None] = mapped_column(JSON)
    drafted_response: Mapped[str | None] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"
    __table_args__ = (UniqueConstraint("investigation_id", "sequence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[str] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    agent: Mapped[str] = mapped_column(String(60))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"
    __table_args__ = (
        UniqueConstraint("investigation_id", "citation_id"),
        UniqueConstraint("investigation_id", "chunk_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[str] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    citation_id: Mapped[str] = mapped_column(String(20))
    document_id: Mapped[str] = mapped_column(String(120))
    chunk_id: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(240))
    source_path: Mapped[str] = mapped_column(String(500))
    excerpt: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class InvestigationSpecialistReport(Base):
    __tablename__ = "investigation_specialist_reports"
    __table_args__ = (UniqueConstraint("investigation_id", "specialist"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[str] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    specialist: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(Text)
    findings: Mapped[list[str]] = mapped_column(JSON)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    proposed_actions: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class InvestigationProposedAction(Base):
    __tablename__ = "investigation_proposed_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(60))
    service: Mapped[str] = mapped_column(String(30))
    tool_name: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    rationale: Mapped[str] = mapped_column(Text)
    arguments: Mapped[dict[str, object]] = mapped_column(JSON)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    result: Mapped[dict[str, object] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    product_area: Mapped[str] = mapped_column(String(60), index=True)
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), index=True)
    source_type: Mapped[str] = mapped_column(String(20))
    source_path: Mapped[str] = mapped_column(String(500))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[str | None] = mapped_column(String(120))
    checksum: Mapped[str] = mapped_column(String(64))


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    heading: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))


class BenchmarkCase(Base):
    __tablename__ = "benchmark_cases"

    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), primary_key=True)
    dataset_version: Mapped[str] = mapped_column(String(30))
    expected_category: Mapped[str] = mapped_column(String(60))
    acceptable_root_causes: Mapped[list[str]] = mapped_column(JSON)
    required_sources: Mapped[list[str]] = mapped_column(JSON)
    prohibited_claims: Mapped[list[str]] = mapped_column(JSON)
    allowed_tools: Mapped[list[str]] = mapped_column(JSON)
    expected_actions: Mapped[list[str]] = mapped_column(JSON)
    escalation_required: Mapped[bool] = mapped_column(Boolean)
