from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from tracedesk_api.config import Settings
from tracedesk_api.investigations.model import (
    FakeInvestigationModel,
    ModelTurn,
    ModelUsage,
    RouterDecision,
    ToolRequest,
)
from tracedesk_api.investigations.schemas import (
    Citation,
    Classification,
    Diagnosis,
    EvidenceView,
    Finding,
    InvestigationPlan,
    ProposedAction,
    SpecialistReport,
)
from tracedesk_api.investigations.workflow import (
    InvestigationWorkflow,
    _clarify_platform_mitigation,
)
from tracedesk_api.mcp_layer.contracts import (
    AuthorizationContext,
    ExplorerCatalog,
    ExplorerServer,
    ExplorerTool,
)


class FakeRepository:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []
        self.evidence: list[EvidenceView] = []
        self.completed: Diagnosis | None = None
        self.error: str | None = None
        self.specialist_reports: list[SpecialistReport] = []
        self.proposed_actions: list[ProposedAction] = []

    async def mark_started(self, investigation_id: str) -> None:
        self.events.append(("investigation.started", {}))

    async def append_event(
        self,
        investigation_id: str,
        event_type: str,
        agent: str,
        payload: dict[str, object],
    ) -> None:
        self.events.append((event_type, payload))

    async def save_classification(self, investigation_id: str, classification: Any) -> None:
        self.events.append(("classification.completed", classification.model_dump()))

    async def save_plan(self, investigation_id: str, plan: Any) -> None:
        self.events.append(("plan.completed", plan.model_dump()))

    async def save_budget(self, investigation_id: str, **values: int) -> None:
        self.events.append(("budget.updated", dict(values)))

    async def add_evidence(
        self, investigation_id: str, item: dict[str, Any]
    ) -> tuple[EvidenceView, bool]:
        existing = next((value for value in self.evidence if value.chunk_id == item["chunk_id"]), None)
        if existing:
            return existing, False
        evidence = EvidenceView(
            citation_id=f"E{len(self.evidence) + 1}",
            document_id=item["document_id"],
            chunk_id=item["chunk_id"],
            title=item["title"],
            source_path=item["source_path"],
            excerpt=item["content"],
            score=item.get("score"),
        )
        self.evidence.append(evidence)
        self.events.append(("evidence.added", evidence.model_dump()))
        return evidence, True

    async def get(self, investigation_id: str) -> SimpleNamespace:
        return SimpleNamespace(evidence=self.evidence)

    async def save_specialist_report(
        self, investigation_id: str, report: SpecialistReport
    ) -> None:
        self.specialist_reports.append(report)
        self.events.append(("specialist.completed", report.model_dump()))

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
        action = ProposedAction(
            id=action_id,
            action_type=action_type,  # type: ignore[arg-type]
            service="support",
            tool_name=tool_name,  # type: ignore[arg-type]
            title=title,
            rationale=rationale,
            arguments=arguments,
            evidence_ids=evidence_ids,
            status="pending",
            result=None,
            error=None,
            created_at=datetime.now(UTC),
            decided_at=None,
            executed_at=None,
        )
        self.proposed_actions.append(action)
        self.events.append(("action.proposed", action.model_dump()))
        return action

    async def complete(self, investigation_id: str, diagnosis: Diagnosis) -> None:
        self.completed = diagnosis
        self.events.append(("investigation.completed", {}))

    async def fail(self, investigation_id: str, message: str) -> None:
        self.error = message
        self.events.append(("investigation.failed", {"message": message}))


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def catalog(self) -> ExplorerCatalog:
        authorization_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "authorization": {"type": "object"},
            },
            "required": ["query", "authorization"],
        }
        return ExplorerCatalog(
            servers=[
                ExplorerServer(
                    name="knowledge",
                    tools=[
                        ExplorerTool(
                            name="search_knowledge",
                            description="Search evidence",
                            input_schema=authorization_schema,
                        )
                    ],
                    resources=[],
                    prompts=[],
                ),
                ExplorerServer(
                    name="operations",
                    tools=[
                        ExplorerTool(
                            name="list_incidents",
                            description="List incidents",
                            input_schema={
                                "type": "object",
                                "properties": {
                                    "region": {"type": "string"},
                                    "authorization": {"type": "object"},
                                },
                                "required": ["authorization"],
                            },
                        )
                    ],
                    resources=[],
                    prompts=[],
                ),
            ]
        )

    async def call_tool(
        self, service: str, tool: str, arguments: dict[str, Any], authorization: Any
    ) -> dict[str, Any]:
        self.calls.append((service, tool))
        if tool == "get_case":
            return {
                "data": {
                    "id": "TKT-1007",
                    "subject": "EU delivery latency",
                    "description": "EU is delayed while US is healthy",
                    "category": "reliability",
                    "organization": {"region": "eu-west"},
                    "integration": None,
                }
            }
        if tool == "list_incidents":
            return {
                "data": [
                    {
                        "id": "INC-001",
                        "title": "EU webhook delivery latency",
                        "status": "monitoring",
                    }
                ]
            }
        return {
            "data": [
                {
                    "chunk_id": "regional-delivery-latency#000",
                    "document_id": "regional-delivery-latency",
                    "title": "Investigating region-specific delivery latency",
                    "source_path": "knowledge/docs/regional-delivery-latency.md",
                    "content": "Queue delay isolated to eu-west with normal execution time.",
                    "score": 0.032,
                }
            ]
        }


def decision() -> RouterDecision:
    return RouterDecision(
        classification=Classification(
            category="reliability",
            urgency="urgent",
            complexity="moderate",
            summary="Regional delivery latency requires incident correlation.",
            rationale="The symptom is isolated to EU while US remains healthy.",
        ),
        plan=InvestigationPlan(
            hypotheses=["Regional queue degradation"],
            evidence_needed=["Current regional latency guidance"],
            allowed_tools=["search_knowledge"],
            steps=["Search current evidence", "Correlate the regional symptom"],
        ),
    )


def diagnosis(evidence_id: str = "E1") -> Diagnosis:
    return Diagnosis(
        summary="The evidence supports an EU regional queue delay.",
        root_cause="Regional queue degradation delayed dispatch.",
        confidence="high",
        findings=[Finding(claim="The delay occurred before dispatch.", evidence_ids=[evidence_id])],
        citations=[Citation(evidence_id=evidence_id, supports="Documents regional queue delay behavior.")],
        proposed_actions=["Avoid endpoint changes and monitor recovery."],
        drafted_response="We identified an EU regional delivery delay and your endpoint does not need changes.",
    )


def test_platform_mitigation_wording_is_attributed_to_platform_team() -> None:
    clarified = _clarify_platform_mitigation(
        diagnosis().model_copy(
            update={
                "summary": "The issue has been mitigated.",
                "drafted_response": "The issue has been resolved.",
            }
        )
    )

    assert "documented as mitigated by the Acme Automations platform team" in clarified.summary
    assert "documented as resolved by the Acme Automations platform team" in clarified.drafted_response


def test_specialist_rationale_is_trimmed_before_validation() -> None:
    report = SpecialistReport(
        specialist="reliability",
        status="completed",
        rationale="The customer reports that " + ("verbose operational context. " * 80),
        findings=["Evidence supports a bounded reliability review."],
        evidence_ids=[],
        proposed_actions=[],
    )

    assert len(report.rationale) <= 1000
    assert report.rationale.endswith("[truncated]")


async def test_workflow_uses_read_tool_and_completes_with_valid_citation() -> None:
    repository = FakeRepository()
    gateway = FakeGateway()
    model = FakeInvestigationModel(
        decision=decision(),
        turns=[
            ModelTurn(
                content=[
                    {"type": "text", "text": "I will check current regional evidence."},
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "search_knowledge",
                        "input": {"query": "EU regional queue latency", "limit": 3},
                    },
                ],
                tool_requests=[
                    ToolRequest(
                        id="tool_1",
                        name="search_knowledge",
                        input={"query": "EU regional queue latency", "limit": 3},
                    )
                ],
                stop_reason="tool_use",
                usage=ModelUsage(input_tokens=100, output_tokens=30),
            ),
            ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=ModelUsage()),
        ],
        diagnosis=diagnosis(),
    )
    workflow = InvestigationWorkflow(
        repository=repository,  # type: ignore[arg-type]
        gateway=gateway,  # type: ignore[arg-type]
        model=model,
        settings=Settings(anthropic_api_key="test-key"),
    )
    await workflow.run("investigation-1", "TKT-1007", authorization())

    assert repository.error is None
    assert repository.completed is not None
    assert [call[1] for call in gateway.calls] == [
        "get_case",
        "search_knowledge",
    ]
    assert repository.evidence[0].citation_id == "E1"
    assert model.last_synthesis_allowed_evidence_ids == ["E1"]
    assert {report.specialist for report in repository.specialist_reports} == {
        "documentation",
        "reliability",
    }
    assert repository.proposed_actions
    assert {call[1] for call in gateway.calls}.isdisjoint(
        {"add_internal_note", "update_ticket_status"}
    )
    assert any(event[0] == "tool.completed" for event in repository.events)


async def test_workflow_rejects_unresolvable_citation() -> None:
    repository = FakeRepository()
    model = FakeInvestigationModel(
        decision=decision(),
        turns=[ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=ModelUsage())],
        diagnosis=diagnosis("E9"),
    )
    workflow = InvestigationWorkflow(
        repository=repository,  # type: ignore[arg-type]
        gateway=FakeGateway(),  # type: ignore[arg-type]
        model=model,
        settings=Settings(anthropic_api_key="test-key"),
    )
    await workflow.run("investigation-2", "TKT-1007", authorization())

    assert repository.completed is None
    assert repository.error is not None
    assert "unknown evidence IDs" in repository.error


async def test_workflow_repairs_mixed_unknown_citation_ids() -> None:
    repository = FakeRepository()
    gateway = FakeGateway()
    mixed_diagnosis = diagnosis().model_copy(
        update={
            "confidence": "high",
            "findings": [
                Finding(
                    claim="The captured evidence supports a regional queue delay.",
                    evidence_ids=["E1", "E11"],
                ),
                Finding(
                    claim="This unsupported claim cites only invented evidence.",
                    evidence_ids=["E12"],
                ),
            ],
            "citations": [
                Citation(evidence_id="E1", supports="Documents regional queue delay behavior."),
                Citation(evidence_id="E11", supports="Invented extra evidence."),
            ],
        }
    )
    model = FakeInvestigationModel(
        decision=decision(),
        turns=[
            ModelTurn(
                content=[
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "search_knowledge",
                        "input": {"query": "EU regional queue latency", "limit": 3},
                    },
                ],
                tool_requests=[
                    ToolRequest(
                        id="tool_1",
                        name="search_knowledge",
                        input={"query": "EU regional queue latency", "limit": 3},
                    )
                ],
                stop_reason="tool_use",
                usage=ModelUsage(input_tokens=100, output_tokens=30),
            ),
            ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=ModelUsage()),
        ],
        diagnosis=mixed_diagnosis,
    )
    workflow = InvestigationWorkflow(
        repository=repository,  # type: ignore[arg-type]
        gateway=gateway,  # type: ignore[arg-type]
        model=model,
        settings=Settings(anthropic_api_key="test-key"),
    )
    await workflow.run("investigation-repair", "TKT-1007", authorization())

    assert repository.error is None
    assert repository.completed is not None
    assert repository.completed.confidence == "medium"
    assert [finding.evidence_ids for finding in repository.completed.findings] == [["E1"]]
    assert [citation.evidence_id for citation in repository.completed.citations] == ["E1"]


async def test_specialist_lane_calls_only_allowed_tools() -> None:
    repository = FakeRepository()
    gateway = FakeGateway()
    model = FakeInvestigationModel(
        decision=decision(),
        turns=[
            ModelTurn(
                content=[
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "search_knowledge",
                        "input": {"query": "EU regional queue latency", "limit": 3},
                    },
                ],
                tool_requests=[
                    ToolRequest(
                        id="tool_1",
                        name="search_knowledge",
                        input={"query": "EU regional queue latency", "limit": 3},
                    )
                ],
                stop_reason="tool_use",
                usage=ModelUsage(input_tokens=100, output_tokens=30),
            ),
            ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=ModelUsage()),
        ],
        specialist_turns={
            "reliability": [
                ModelTurn(
                    content=[
                        {
                            "type": "tool_use",
                            "id": "tool_rel_1",
                            "name": "list_incidents",
                            "input": {"region": "eu"},
                        },
                    ],
                    tool_requests=[
                        ToolRequest(
                            id="tool_rel_1",
                            name="list_incidents",
                            input={"region": "eu"},
                        )
                    ],
                    stop_reason="tool_use",
                    usage=ModelUsage(input_tokens=90, output_tokens=20),
                ),
                ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=ModelUsage()),
            ]
        },
        diagnosis=diagnosis(),
    )
    workflow = InvestigationWorkflow(
        repository=repository,  # type: ignore[arg-type]
        gateway=gateway,  # type: ignore[arg-type]
        model=model,
        settings=Settings(anthropic_api_key="test-key"),
    )
    await workflow.run("investigation-specialist", "TKT-1007", authorization())

    assert repository.error is None
    assert [call[1] for call in gateway.calls] == [
        "get_case",
        "list_incidents",
        "search_knowledge",
    ]
    assert any(
        event[0] == "tool.requested" and event[1]["tool"] == "list_incidents"
        for event in repository.events
    )


def authorization() -> AuthorizationContext:
    return AuthorizationContext(
        request_id="request_12345678",
        persona_id="persona_maya",
        scopes=["support:read", "knowledge:read", "operations:read"],
    )
