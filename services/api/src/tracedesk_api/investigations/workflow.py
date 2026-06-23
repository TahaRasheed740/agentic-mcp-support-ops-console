from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from tracedesk_api.config import Settings
from tracedesk_api.investigations.model import InvestigationModel, ModelUsage, RetryCallback
from tracedesk_api.investigations.repository import InvestigationRepository
from tracedesk_api.investigations.schemas import (
    Diagnosis,
    EvidenceView,
    InvestigationPlan,
    SpecialistName,
    SpecialistReport,
)
from tracedesk_api.mcp_layer.contracts import AuthorizationContext, ServiceName
from tracedesk_api.mcp_layer.gateway import MCPGateway


class InvestigationBudgetExceeded(RuntimeError):
    pass


@dataclass
class Budget:
    token_limit: int
    tool_limit: int
    usage: ModelUsage
    tool_calls: int = 0

    def add_usage(self, usage: ModelUsage) -> None:
        self.usage.add(usage)
        if self.usage.total > self.token_limit:
            raise InvestigationBudgetExceeded(
                f"Investigation token budget exceeded ({self.usage.total}/{self.token_limit})"
            )

    def use_tool(self) -> None:
        self.tool_calls += 1
        if self.tool_calls > self.tool_limit:
            raise InvestigationBudgetExceeded(
                f"Investigation tool-call budget exceeded ({self.tool_calls}/{self.tool_limit})"
            )


class InvestigationWorkflow:
    def __init__(
        self,
        *,
        repository: InvestigationRepository,
        gateway: MCPGateway,
        model: InvestigationModel,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.gateway = gateway
        self.model = model
        self.settings = settings

    async def run(
        self,
        investigation_id: str,
        case_id: str,
        authorization: AuthorizationContext,
    ) -> None:
        budget = Budget(
            token_limit=self.settings.investigation_token_budget,
            tool_limit=self.settings.investigation_max_tool_calls,
            usage=ModelUsage(),
        )
        try:
            await self.repository.mark_started(investigation_id)
            case_result = await self.gateway.call_tool(
                "support", "get_case", {"case_id": case_id}, authorization
            )
            case_context = dict(case_result["data"])

            async def on_retry(attempt: int, delay: float, reason: str) -> None:
                await self.repository.append_event(
                    investigation_id,
                    "retry.scheduled",
                    "workflow",
                    {"attempt": attempt, "delay_seconds": delay, "reason": reason},
                )

            decision, router_usage = await self.model.classify_and_plan(
                case_context, on_retry
            )
            budget.add_usage(router_usage)
            await self.repository.save_classification(
                investigation_id, decision.classification
            )
            await self.repository.save_plan(investigation_id, decision.plan)
            await self._save_budget(investigation_id, budget)
            specialist_reports = await self._run_specialists(
                investigation_id,
                case_context,
                decision.plan,
                authorization,
                budget,
            )
            await self._save_budget(investigation_id, budget)

            catalog = await self.gateway.catalog()
            tool_map, tools = _tool_catalog(catalog, set(decision.plan.allowed_tools))
            if "search_knowledge" not in tool_map:
                raise ValueError("The investigation plan must permit knowledge search")

            messages: list[dict[str, Any]] = [
                {
                    "role": "user",
                    "content": "Investigate this case according to the approved read-only plan:\n"
                    + json.dumps(
                    {
                        "case": case_context,
                        "classification": decision.classification.model_dump(mode="json"),
                        "plan": decision.plan.model_dump(mode="json"),
                    },
                    default=str,
                    separators=(",", ":"),
                ),
            }
        ]
            investigation_log: list[dict[str, Any]] = []
            await self.repository.append_event(
                investigation_id,
                "agent.started",
                "investigator",
                {
                    "model": self.settings.claude_investigator_model,
                    "allowed_tools": sorted(tool_map),
                },
            )

            for round_number in range(1, self.settings.investigation_max_rounds + 1):
                text_buffer = TextEventBuffer(self.repository, investigation_id)
                turn = await self.model.investigate(
                    messages, tools, text_buffer.push, on_retry
                )
                await text_buffer.flush()
                budget.add_usage(turn.usage)
                messages.append({"role": "assistant", "content": turn.content})
                investigation_log.append(
                    {
                        "round": round_number,
                        "stop_reason": turn.stop_reason,
                        "tool_requests": [request.name for request in turn.tool_requests],
                    }
                )
                if not turn.tool_requests:
                    await self._save_budget(investigation_id, budget)
                    break

                tool_results: list[dict[str, Any]] = []
                for request in turn.tool_requests:
                    if request.name not in tool_map:
                        raise ValueError(f"Claude requested a tool outside the plan: {request.name}")
                    budget.use_tool()
                    arguments = _bounded_arguments(request.name, request.input)
                    await self.repository.append_event(
                        investigation_id,
                        "tool.requested",
                        "investigator",
                        {
                            "tool_call_id": request.id,
                            "tool": request.name,
                            "service": tool_map[request.name],
                            "arguments": arguments,
                        },
                    )
                    result = await self.gateway.call_tool(
                        tool_map[request.name], request.name, arguments, authorization
                    )
                    await self._capture_evidence(investigation_id, request.name, result)
                    compact_result = _compact_tool_result(request.name, result)
                    await self.repository.append_event(
                        investigation_id,
                        "tool.completed",
                        "investigator",
                        {
                            "tool_call_id": request.id,
                            "tool": request.name,
                            "service": tool_map[request.name],
                            "result": compact_result,
                        },
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": request.id,
                            "content": json.dumps(
                                compact_result, default=str, separators=(",", ":")
                            ),
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
                await self._save_budget(investigation_id, budget)
            else:
                investigation_log.append({"round_limit_reached": True})

            view = await self.repository.get(investigation_id)
            if view is None:
                raise ValueError("Investigation disappeared during execution")
            if not view.evidence:
                fallback = await self.gateway.call_tool(
                    "knowledge",
                    "search_knowledge",
                    {
                        "query": f"{case_context['subject']} {case_context['description']}",
                        "limit": 5,
                        "mode": "hybrid",
                    },
                    authorization,
                )
                budget.use_tool()
                await self._capture_evidence(investigation_id, "search_knowledge", fallback)
                investigation_log.append(
                    {"fallback": "deterministic evidence search after model stopped without evidence"}
                )
                view = await self.repository.get(investigation_id)
                assert view is not None

            evidence_payload = []
            for item in view.evidence:
                payload = item.model_dump(mode="json")
                payload["excerpt"] = _clip_text(item.excerpt, 900)
                evidence_payload.append(payload)
            diagnosis, synthesis_usage = await self.model.synthesize(
                case_context,
                decision.plan,
                specialist_reports,
                evidence_payload,
                [item.citation_id for item in view.evidence],
                investigation_log,
                on_retry,
            )
            diagnosis = _clarify_platform_mitigation(diagnosis)
            diagnosis = _repair_diagnosis_citations(diagnosis, view.evidence)
            budget.add_usage(synthesis_usage)
            _validate_citations(diagnosis, view.evidence)
            await self._save_budget(investigation_id, budget)
            await self._create_actions_from_diagnosis(
                investigation_id,
                case_id,
                diagnosis,
                view.evidence,
            )
            await self.repository.complete(investigation_id, diagnosis)
        except Exception as error:
            await self.repository.fail(investigation_id, str(error))

    async def _run_specialists(
        self,
        investigation_id: str,
        case_context: dict[str, Any],
        plan: InvestigationPlan,
        authorization: AuthorizationContext,
        budget: Budget,
    ) -> list[SpecialistReport]:
        specialists = _route_specialists(case_context, plan)
        if not specialists:
            return []
        for specialist in specialists:
            await self.repository.append_event(
                investigation_id,
                "specialist.started",
                specialist,
                {"specialist": specialist, "mode": "claude_bounded_read_only"},
            )
        reports = await asyncio.gather(
            *[
                self._run_specialist(
                    investigation_id,
                    specialist,
                    case_context,
                    authorization,
                    budget,
                )
                for specialist in specialists
            ]
        )
        for report in reports:
            await self.repository.save_specialist_report(investigation_id, report)
        conflicts = _detect_conflicts(reports)
        await self.repository.append_event(
            investigation_id,
            "specialist.reconciled",
            "workflow",
            {"specialists": [report.specialist for report in reports], "conflicts": conflicts},
        )
        return reports

    async def _run_specialist(
        self,
        investigation_id: str,
        specialist: SpecialistName,
        case_context: dict[str, Any],
        authorization: AuthorizationContext,
        budget: Budget,
    ) -> SpecialistReport:
        catalog = await self.gateway.catalog()
        tool_map, tools = _specialist_tool_catalog(catalog, specialist)
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "specialist": specialist,
                        "case": case_context,
                        "instruction": (
                            "Investigate only your specialist lane. Use read-only tools, "
                            "collect evidence, then stop for structured report synthesis."
                        ),
                        "available_tools": sorted(tool_map),
                    },
                    default=str,
                    separators=(",", ":"),
                ),
            }
        ]
        specialist_log: list[dict[str, Any]] = []
        for round_number in range(1, self.settings.investigation_specialist_max_rounds + 1):
            text_buffer = TextEventBuffer(self.repository, investigation_id, specialist)
            turn = await self.model.investigate_specialist(
                specialist,
                messages,
                tools,
                text_buffer.push,
                self._retry_event(investigation_id, specialist),
            )
            await text_buffer.flush()
            budget.add_usage(turn.usage)
            messages.append({"role": "assistant", "content": turn.content})
            specialist_log.append(
                {
                    "round": round_number,
                    "stop_reason": turn.stop_reason,
                    "tool_requests": [request.name for request in turn.tool_requests],
                }
            )
            if not turn.tool_requests:
                break

            tool_results: list[dict[str, Any]] = []
            for request in turn.tool_requests:
                if request.name not in tool_map:
                    raise ValueError(
                        f"{specialist} specialist requested a tool outside its lane: {request.name}"
                    )
                budget.use_tool()
                arguments = _bounded_arguments(request.name, request.input)
                await self.repository.append_event(
                    investigation_id,
                    "tool.requested",
                    specialist,
                    {
                        "tool_call_id": request.id,
                        "tool": request.name,
                        "service": tool_map[request.name],
                        "arguments": arguments,
                    },
                )
                result = await self.gateway.call_tool(
                    tool_map[request.name], request.name, arguments, authorization
                )
                await self._capture_evidence(investigation_id, request.name, result)
                compact_result = _compact_tool_result(request.name, result)
                await self.repository.append_event(
                    investigation_id,
                    "tool.completed",
                    specialist,
                    {
                        "tool_call_id": request.id,
                        "tool": request.name,
                        "service": tool_map[request.name],
                        "result": compact_result,
                    },
                )
                specialist_log.append(
                    {
                        "tool": request.name,
                        "service": tool_map[request.name],
                        "arguments": arguments,
                        "result": compact_result,
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": request.id,
                        "content": json.dumps(
                            compact_result, default=str, separators=(",", ":")
                        ),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            await self._save_budget(investigation_id, budget)

        view = await self.repository.get(investigation_id)
        evidence_payload = []
        if view is not None:
            for item in view.evidence:
                payload = item.model_dump(mode="json")
                payload["excerpt"] = _clip_text(item.excerpt, 900)
                evidence_payload.append(payload)
        report, usage = await self.model.synthesize_specialist(
            specialist,
            case_context,
            specialist_log,
            evidence_payload,
            self._retry_event(investigation_id, specialist),
        )
        budget.add_usage(usage)
        return _sanitize_specialist_report(report, view.evidence if view else [])

    def _retry_event(self, investigation_id: str, agent: str) -> RetryCallback:
        async def on_retry(attempt: int, delay: float, reason: str) -> None:
            await self.repository.append_event(
                investigation_id,
                "retry.scheduled",
                agent,
                {"attempt": attempt, "delay_seconds": delay, "reason": reason},
            )

        return on_retry

    async def _create_actions_from_diagnosis(
        self,
        investigation_id: str,
        case_id: str,
        diagnosis: Diagnosis,
        evidence: list[EvidenceView],
    ) -> None:
        evidence_ids = [item.citation_id for item in evidence[:3]]
        note_recommendations: list[str] = []
        status_recommendations: list[str] = []
        for recommendation in diagnosis.proposed_actions[:5]:
            lowered = recommendation.lower()
            if "mark" in lowered and ("resolved" in lowered or "resolve" in lowered):
                status_recommendations.append(recommendation)
            else:
                note_recommendations.append(recommendation)
        if note_recommendations:
            await self.repository.create_proposed_action(
                investigation_id,
                action_id=f"act_{uuid4().hex}",
                action_type="add_internal_note",
                tool_name="add_internal_note",
                title="Add consolidated investigation note",
                rationale="Record the investigation outcome and recommended support guidance in the ticket.",
                arguments={
                    "case_id": case_id,
                    "note": "TraceDesk investigation recommendations:\n"
                    + "\n".join(f"- {item}" for item in note_recommendations),
                },
                evidence_ids=evidence_ids,
                idempotency_key=f"{investigation_id}:internal-note",
            )
        if status_recommendations:
            await self.repository.create_proposed_action(
                investigation_id,
                action_id=f"act_{uuid4().hex}",
                action_type="update_ticket_status",
                tool_name="update_ticket_status",
                title="Mark ticket resolved",
                rationale=status_recommendations[0],
                arguments={"case_id": case_id, "status": "resolved"},
                evidence_ids=evidence_ids,
                idempotency_key=f"{investigation_id}:status-resolved",
            )

    async def _capture_evidence(
        self,
        investigation_id: str,
        tool_name: str,
        result: dict[str, Any],
    ) -> None:
        data = result.get("data")
        if tool_name == "search_knowledge" and isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    await self.repository.add_evidence(investigation_id, item)
        elif tool_name == "get_document" and isinstance(data, dict):
            for chunk in data.get("chunks", []):
                if isinstance(chunk, dict):
                    await self.repository.add_evidence(
                        investigation_id,
                        {
                            "chunk_id": chunk["id"],
                            "document_id": data["id"],
                            "title": data["title"],
                            "source_path": data["source_path"],
                            "content": chunk["content"],
                            "score": None,
                        },
                    )

    async def _save_budget(self, investigation_id: str, budget: Budget) -> None:
        await self.repository.save_budget(
            investigation_id,
            input_tokens=budget.usage.input_tokens,
            output_tokens=budget.usage.output_tokens,
            cache_read_tokens=budget.usage.cache_read_tokens,
            cache_creation_tokens=budget.usage.cache_creation_tokens,
            tool_calls=budget.tool_calls,
        )


class TextEventBuffer:
    def __init__(
        self,
        repository: InvestigationRepository,
        investigation_id: str,
        agent: str = "investigator",
    ) -> None:
        self.repository = repository
        self.investigation_id = investigation_id
        self.agent = agent
        self.buffer = ""

    async def push(self, text: str) -> None:
        self.buffer += text
        if len(self.buffer) >= 120 or self.buffer.endswith((". ", "? ", "! ", "\n")):
            await self.flush()

    async def flush(self) -> None:
        if not self.buffer:
            return
        text, self.buffer = self.buffer, ""
        await self.repository.append_event(
            self.investigation_id,
            "model.text_delta",
            self.agent,
            {"text": text},
        )


def _tool_catalog(catalog: Any, allowed: set[str]) -> tuple[dict[str, ServiceName], list[dict[str, Any]]]:
    tool_map: dict[str, ServiceName] = {}
    tools: list[dict[str, Any]] = []
    for server in catalog.servers:
        for tool in server.tools:
            if tool.name not in allowed or tool.name in {
                "get_case",
                "get_document",
                "update_ticket_status",
                "add_internal_note",
            }:
                continue
            schema = json.loads(json.dumps(tool.input_schema))
            schema.get("properties", {}).pop("authorization", None)
            required = schema.get("required", [])
            schema["required"] = [item for item in required if item != "authorization"]
            tool_map[tool.name] = server.name
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or f"Call the {tool.name} MCP tool",
                    "input_schema": schema,
                }
            )
    return tool_map, tools


def _specialist_tool_catalog(
    catalog: Any, specialist: SpecialistName
) -> tuple[dict[str, ServiceName], list[dict[str, Any]]]:
    allowed_by_specialist: dict[SpecialistName, set[str]] = {
        "documentation": {"search_knowledge", "get_document"},
        "account": {"get_integration"},
        "reliability": {"get_integration", "list_recent_runs", "get_run_logs", "list_incidents"},
    }
    allowed = allowed_by_specialist[specialist]
    tool_map: dict[str, ServiceName] = {}
    tools: list[dict[str, Any]] = []
    for server in catalog.servers:
        for tool in server.tools:
            if tool.name not in allowed:
                continue
            schema = json.loads(json.dumps(tool.input_schema))
            schema.get("properties", {}).pop("authorization", None)
            required = schema.get("required", [])
            schema["required"] = [item for item in required if item != "authorization"]
            tool_map[tool.name] = server.name
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or f"Call the {tool.name} MCP tool",
                    "input_schema": schema,
                }
            )
    return tool_map, tools


def _route_specialists(
    case_context: dict[str, Any], plan: InvestigationPlan
) -> list[SpecialistName]:
    text = f"{case_context.get('subject', '')} {case_context.get('description', '')}".lower()
    category = str(case_context.get("category", "")).lower()
    allowed = set(plan.allowed_tools)
    specialists: list[SpecialistName] = ["documentation"]
    if case_context.get("integration") or category in {"authentication", "account", "billing"}:
        specialists.append("account")
    reliability_terms = ("latency", "delay", "incident", "run", "failed", "queue", "timeout")
    if (
        category == "reliability"
        or any(term in text for term in reliability_terms)
        or {"list_incidents", "list_recent_runs", "get_run_logs"} & allowed
    ):
        specialists.append("reliability")
    return specialists


def _detect_conflicts(reports: list[SpecialistReport]) -> list[str]:
    findings = " ".join(" ".join(report.findings).lower() for report in reports)
    conflicts: list[str] = []
    if "no reliability-specific records" in findings and "incident records" in findings:
        conflicts.append("Reliability findings disagree about incident correlation.")
    if "healthy" in findings and "failed" in findings:
        conflicts.append("Account or reliability findings include both healthy and failed signals.")
    return conflicts


def _bounded_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    bounded = dict(arguments)
    if tool_name == "search_knowledge":
        bounded["limit"] = min(int(bounded.get("limit", 5)), 5)
    elif "limit" in bounded:
        bounded["limit"] = min(int(bounded["limit"]), 25)
    return bounded


def _compact_tool_result(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data")
    compact: dict[str, Any] = {
        "service": result.get("service"),
        "request_id": result.get("request_id"),
    }
    if tool_name == "search_knowledge" and isinstance(data, list):
        compact["data"] = [
            _pick_and_clip(
                item,
                {
                    "chunk_id",
                    "document_id",
                    "title",
                    "source_path",
                    "status",
                    "version",
                    "score",
                    "rrf_score",
                    "semantic_rank",
                    "lexical_rank",
                    "content",
                },
                text_limit=650,
            )
            for item in data[:4]
            if isinstance(item, dict)
        ]
    elif tool_name == "get_document" and isinstance(data, dict):
        chunks = data.get("chunks", [])
        compact["data"] = _pick_and_clip(
            data,
            {"id", "title", "source_path", "status", "version", "product_area"},
            text_limit=400,
        )
        if isinstance(chunks, list):
            compact["data"]["chunks"] = [
                _pick_and_clip(
                    chunk,
                    {"id", "heading", "chunk_index", "content"},
                    text_limit=650,
                )
                for chunk in chunks[:4]
                if isinstance(chunk, dict)
            ]
    elif tool_name in {"list_recent_runs", "get_run_logs", "list_incidents"} and isinstance(data, list):
        limits = {"list_recent_runs": 8, "get_run_logs": 12, "list_incidents": 6}
        compact["data"] = [
            _compact_record(item, text_limit=500)
            for item in data[: limits[tool_name]]
            if isinstance(item, dict)
        ]
    elif tool_name == "get_integration" and isinstance(data, dict):
        compact["data"] = _pick_and_clip(
            data,
            {
                "id",
                "organization_id",
                "name",
                "kind",
                "status",
                "environment",
                "last_seen_at",
                "region",
            },
            text_limit=500,
        )
    else:
        compact["data"] = _compact_value(data, text_limit=500)
    return compact


def _compact_record(record: dict[str, Any], text_limit: int) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in record.items():
        if key in {"payload", "request_body", "response_body", "raw", "metadata"}:
            continue
        compact[key] = _compact_value(value, text_limit=text_limit)
    return compact


def _pick_and_clip(
    record: dict[str, Any],
    allowed_keys: set[str],
    *,
    text_limit: int,
) -> dict[str, Any]:
    return {
        key: _compact_value(value, text_limit=text_limit)
        for key, value in record.items()
        if key in allowed_keys
    }


def _compact_value(value: Any, *, text_limit: int) -> Any:
    if isinstance(value, str):
        return _clip_text(value, text_limit)
    if isinstance(value, list):
        return [_compact_value(item, text_limit=text_limit) for item in value[:12]]
    if isinstance(value, dict):
        return _compact_record(value, text_limit=text_limit)
    return value


def _clip_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + " ... [truncated]"


def _validate_citations(diagnosis: Diagnosis, evidence: list[EvidenceView]) -> None:
    valid_ids = {item.citation_id for item in evidence}
    cited_ids = {citation.evidence_id for citation in diagnosis.citations}
    finding_ids = {item for finding in diagnosis.findings for item in finding.evidence_ids}
    invalid = (cited_ids | finding_ids) - valid_ids
    if invalid:
        raise ValueError(f"Diagnosis cited unknown evidence IDs: {sorted(invalid)}")
    if not cited_ids:
        raise ValueError("Diagnosis must include at least one resolvable citation")


def _repair_diagnosis_citations(
    diagnosis: Diagnosis, evidence: list[EvidenceView]
) -> Diagnosis:
    valid_ids = {item.citation_id for item in evidence}
    cited_ids = {citation.evidence_id for citation in diagnosis.citations}
    finding_ids = {item for finding in diagnosis.findings for item in finding.evidence_ids}
    if not ((cited_ids | finding_ids) - valid_ids):
        return diagnosis

    repaired_findings = []
    for finding in diagnosis.findings:
        evidence_ids = [item for item in finding.evidence_ids if item in valid_ids]
        if evidence_ids:
            repaired_findings.append(finding.model_copy(update={"evidence_ids": evidence_ids}))
    repaired_citations = [
        citation for citation in diagnosis.citations if citation.evidence_id in valid_ids
    ]

    if not repaired_findings or not repaired_citations:
        return diagnosis

    confidence = "medium" if diagnosis.confidence == "high" else diagnosis.confidence
    return diagnosis.model_copy(
        update={
            "findings": repaired_findings,
            "citations": repaired_citations,
            "confidence": confidence,
        }
    )


def _sanitize_specialist_report(
    report: SpecialistReport, evidence: list[EvidenceView]
) -> SpecialistReport:
    valid_ids = {item.citation_id for item in evidence}
    return report.model_copy(
        update={
            "evidence_ids": [
                evidence_id for evidence_id in report.evidence_ids if evidence_id in valid_ids
            ],
            "status": "completed" if report.status == "skipped" else report.status,
        }
    )


def _clarify_platform_mitigation(diagnosis: Diagnosis) -> Diagnosis:
    def clarify(text: str) -> str:
        replacements = {
            "has been mitigated": (
                "is documented as mitigated by the Acme Automations platform team"
            ),
            "have been mitigated": (
                "are documented as mitigated by the Acme Automations platform team"
            ),
            "has been resolved": (
                "is documented as resolved by the Acme Automations platform team"
            ),
            "have been resolved": (
                "are documented as resolved by the Acme Automations platform team"
            ),
        }
        updated = text
        for ambiguous, clarified in replacements.items():
            updated = updated.replace(ambiguous, clarified)
        return updated

    return diagnosis.model_copy(
        update={
            "summary": clarify(diagnosis.summary),
            "root_cause": clarify(diagnosis.root_cause),
            "findings": [
                finding.model_copy(update={"claim": clarify(finding.claim)})
                for finding in diagnosis.findings
            ],
            "citations": [
                citation.model_copy(update={"supports": clarify(citation.supports)})
                for citation in diagnosis.citations
            ],
            "proposed_actions": [
                clarify(action) for action in diagnosis.proposed_actions
            ],
            "drafted_response": clarify(diagnosis.drafted_response),
        }
    )
