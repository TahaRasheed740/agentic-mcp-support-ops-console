from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from anthropic import (
    APIConnectionError,
    APITimeoutError,
    AsyncAnthropic,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel

from tracedesk_api.config import Settings
from tracedesk_api.investigations.schemas import (
    Classification,
    Diagnosis,
    InvestigationPlan,
    SpecialistName,
    SpecialistReport,
)

TextCallback = Callable[[str], Awaitable[None]]
RetryCallback = Callable[[int, float, str], Awaitable[None]]


class RouterDecision(BaseModel):
    classification: Classification
    plan: InvestigationPlan


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_creation_tokens
        )

    def add(self, other: ModelUsage) -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_creation_tokens += other.cache_creation_tokens


@dataclass
class ToolRequest:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ModelTurn:
    content: list[dict[str, Any]]
    tool_requests: list[ToolRequest]
    stop_reason: str | None
    usage: ModelUsage


class InvestigationModel(Protocol):
    async def classify_and_plan(
        self,
        case_context: dict[str, Any],
        on_retry: RetryCallback,
    ) -> tuple[RouterDecision, ModelUsage]: ...

    async def investigate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn: ...

    async def investigate_specialist(
        self,
        specialist: SpecialistName,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn: ...

    async def synthesize_specialist(
        self,
        specialist: SpecialistName,
        case_context: dict[str, Any],
        specialist_log: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[SpecialistReport, ModelUsage]: ...

    async def synthesize(
        self,
        case_context: dict[str, Any],
        plan: InvestigationPlan,
        specialist_reports: list[SpecialistReport],
        evidence: list[dict[str, Any]],
        allowed_evidence_ids: list[str],
        investigation_log: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[Diagnosis, ModelUsage]: ...


class AnthropicInvestigationModel:
    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for live investigations")
        self.settings = settings
        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.claude_request_timeout_seconds,
            max_retries=0,
        )

    async def classify_and_plan(
        self,
        case_context: dict[str, Any],
        on_retry: RetryCallback,
    ) -> tuple[RouterDecision, ModelUsage]:
        async def request() -> Any:
            return await self.client.messages.parse(
                model=self.settings.claude_router_model,
                max_tokens=1200,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": ROUTER_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": "Classify and plan this support case:\n"
                        + _json_text(case_context),
                    }
                ],
                output_format=RouterDecision,
            )

        message = await self._retry(request, on_retry)
        parsed = _parsed_output(message, RouterDecision)
        return parsed, _usage(message.usage)

    async def investigate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn:
        async def request() -> ModelTurn:
            async with self.client.messages.stream(
                model=self.settings.claude_investigator_model,
                max_tokens=1600,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": INVESTIGATOR_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=cast(Any, messages),
                tools=cast(Any, tools),
            ) as stream:
                async for text in stream.text_stream:
                    await on_text(text)
                message = await stream.get_final_message()
            content = [_message_block(block) for block in message.content]
            tool_requests = [
                ToolRequest(id=block.id, name=block.name, input=dict(block.input))
                for block in message.content
                if block.type == "tool_use"
            ]
            return ModelTurn(
                content=content,
                tool_requests=tool_requests,
                stop_reason=message.stop_reason,
                usage=_usage(message.usage),
            )

        return cast(ModelTurn, await self._retry(request, on_retry))

    async def investigate_specialist(
        self,
        specialist: SpecialistName,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn:
        async def request() -> ModelTurn:
            async with self.client.messages.stream(
                model=self.settings.claude_investigator_model,
                max_tokens=1200,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": _specialist_prompt(specialist),
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=cast(Any, messages),
                tools=cast(Any, tools),
            ) as stream:
                async for text in stream.text_stream:
                    await on_text(text)
                message = await stream.get_final_message()
            content = [_message_block(block) for block in message.content]
            tool_requests = [
                ToolRequest(id=block.id, name=block.name, input=dict(block.input))
                for block in message.content
                if block.type == "tool_use"
            ]
            return ModelTurn(
                content=content,
                tool_requests=tool_requests,
                stop_reason=message.stop_reason,
                usage=_usage(message.usage),
            )

        return cast(ModelTurn, await self._retry(request, on_retry))

    async def synthesize_specialist(
        self,
        specialist: SpecialistName,
        case_context: dict[str, Any],
        specialist_log: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[SpecialistReport, ModelUsage]:
        async def request() -> Any:
            return await self.client.messages.parse(
                model=self.settings.claude_investigator_model,
                max_tokens=1200,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": SPECIALIST_REPORT_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": _json_text(
                            {
                                "required_specialist": specialist,
                                "case": case_context,
                                "specialist_log": specialist_log,
                                "evidence": evidence,
                            }
                        ),
                    }
                ],
                output_format=SpecialistReport,
            )

        message = await self._retry(request, on_retry)
        report = _parsed_output(message, SpecialistReport)
        if report.specialist != specialist:
            report = report.model_copy(update={"specialist": specialist})
        return report, _usage(message.usage)

    async def synthesize(
        self,
        case_context: dict[str, Any],
        plan: InvestigationPlan,
        specialist_reports: list[SpecialistReport],
        evidence: list[dict[str, Any]],
        allowed_evidence_ids: list[str],
        investigation_log: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[Diagnosis, ModelUsage]:
        async def request() -> Any:
            return await self.client.messages.parse(
                model=self.settings.claude_investigator_model,
                max_tokens=2200,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": SYNTHESIS_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": _json_text(
                            {
                                "case": case_context,
                                "plan": plan.model_dump(mode="json"),
                                "specialist_reports": [
                                    report.model_dump(mode="json")
                                    for report in specialist_reports
                                ],
                                "citation_contract": {
                                    "allowed_evidence_ids": allowed_evidence_ids,
                                    "rules": [
                                        "Only these IDs may appear in citations or finding.evidence_ids.",
                                        "Reuse IDs when one source supports multiple findings.",
                                        "Omit unsupported claims instead of inventing new IDs.",
                                        "Specialist reports can inform wording but are not citation sources.",
                                    ],
                                },
                                "evidence": evidence,
                                "investigation_log": investigation_log,
                            }
                        ),
                    }
                ],
                output_format=Diagnosis,
            )

        message = await self._retry(request, on_retry)
        return _parsed_output(message, Diagnosis), _usage(message.usage)

    async def _retry(
        self,
        operation: Callable[[], Awaitable[Any]],
        on_retry: RetryCallback,
    ) -> Any:
        retryable = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
        for attempt in range(3):
            try:
                return await operation()
            except retryable as error:
                if attempt == 2:
                    raise
                delay = self._retry_delay(error, attempt)
                await on_retry(attempt + 1, delay, type(error).__name__)
                await asyncio.sleep(delay)
        raise RuntimeError("Model retry loop exhausted")

    def _retry_delay(self, error: Exception, attempt: int) -> float:
        if isinstance(error, RateLimitError):
            return _rate_limit_retry_delay(error, self.settings.claude_rate_limit_retry_seconds)
        return float(2**attempt)


@dataclass
class FakeInvestigationModel:
    decision: RouterDecision
    turns: list[ModelTurn]
    diagnosis: Diagnosis
    usage: ModelUsage = field(default_factory=lambda: ModelUsage(input_tokens=100, output_tokens=50))
    specialist_turns: dict[SpecialistName, list[ModelTurn]] = field(default_factory=dict)
    last_synthesis_allowed_evidence_ids: list[str] = field(default_factory=list)

    async def classify_and_plan(
        self, case_context: dict[str, Any], on_retry: RetryCallback
    ) -> tuple[RouterDecision, ModelUsage]:
        return self.decision, self.usage

    async def investigate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn:
        if not self.turns:
            return ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=self.usage)
        turn = self.turns.pop(0)
        for block in turn.content:
            if block.get("type") == "text":
                await on_text(str(block.get("text", "")))
        return turn

    async def investigate_specialist(
        self,
        specialist: SpecialistName,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback,
        on_retry: RetryCallback,
    ) -> ModelTurn:
        turns = self.specialist_turns.get(specialist)
        if not turns:
            return ModelTurn(content=[], tool_requests=[], stop_reason="end_turn", usage=self.usage)
        turn = turns.pop(0)
        for block in turn.content:
            if block.get("type") == "text":
                await on_text(str(block.get("text", "")))
        return turn

    async def synthesize_specialist(
        self,
        specialist: SpecialistName,
        case_context: dict[str, Any],
        specialist_log: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[SpecialistReport, ModelUsage]:
        evidence_ids = [
            str(item["citation_id"])
            for item in evidence
            if isinstance(item.get("citation_id"), str)
        ][:3]
        return (
            SpecialistReport(
                specialist=specialist,
                status="completed",
                rationale=f"{specialist.title()} specialist reviewed its bounded context.",
                findings=[f"{specialist.title()} specialist found relevant context."],
                evidence_ids=evidence_ids,
                proposed_actions=[],
            ),
            self.usage,
        )

    async def synthesize(
        self,
        case_context: dict[str, Any],
        plan: InvestigationPlan,
        specialist_reports: list[SpecialistReport],
        evidence: list[dict[str, Any]],
        allowed_evidence_ids: list[str],
        investigation_log: list[dict[str, Any]],
        on_retry: RetryCallback,
    ) -> tuple[Diagnosis, ModelUsage]:
        self.last_synthesis_allowed_evidence_ids = allowed_evidence_ids
        return self.diagnosis, self.usage


def _usage(usage: Any) -> ModelUsage:
    return ModelUsage(
        input_tokens=int(usage.input_tokens),
        output_tokens=int(usage.output_tokens),
        cache_read_tokens=int(usage.cache_read_input_tokens or 0),
        cache_creation_tokens=int(usage.cache_creation_input_tokens or 0),
    )


def _message_block(block: Any) -> dict[str, Any]:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": dict(block.input),
        }
    raise ValueError(f"Unsupported Claude content block in tool loop: {block.type}")


def _parsed_output(message: Any, expected: type[BaseModel]) -> Any:
    for block in message.content:
        if block.type == "text" and block.parsed_output is not None:
            if isinstance(block.parsed_output, expected):
                return block.parsed_output
    raise ValueError(f"Claude did not return the required {expected.__name__} structure")


def _json_text(value: object) -> str:
    import json

    return json.dumps(value, default=str, separators=(",", ":"))


def _rate_limit_retry_delay(error: Exception, fallback: float) -> float:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return max(float(retry_after), 1.0)
        except ValueError:
            pass
    for key in (
        "anthropic-ratelimit-input-tokens-reset",
        "anthropic-ratelimit-requests-reset",
        "anthropic-ratelimit-tokens-reset",
    ):
        raw_reset = headers.get(key)
        if not raw_reset:
            continue
        try:
            reset_at = datetime.fromisoformat(raw_reset.replace("Z", "+00:00"))
        except ValueError:
            continue
        return max((reset_at - datetime.now(UTC)).total_seconds() + 1.0, 1.0)
    return fallback


ROUTER_SYSTEM_PROMPT = """You are TraceDesk's support triage router for the fictional Acme Automations SaaS.
Classify only from supplied case facts. Build a compact investigation plan for one general read-only investigator.
Select allowed tools only from: search_knowledge, get_integration,
list_recent_runs, get_run_logs, list_incidents. Do not diagnose yet and never propose a write tool."""

INVESTIGATOR_SYSTEM_PROMPT = """You are TraceDesk's evidence-grounded support investigator.
The case and full text of every search result are already supplied, so never re-fetch either. Use only the supplied
read-only tools. Search current documentation, inspect the smallest relevant operational
context, and stop when evidence is sufficient. Briefly state what you are checking in ordinary support language;
do not reveal hidden reasoning or chain-of-thought. Never claim a fact that is absent from tool results. Never call
write tools, retry jobs, or mutate customer state. Evidence identifiers will be assigned by TraceDesk."""

DOCUMENTATION_SPECIALIST_PROMPT = """You are TraceDesk's documentation specialist for Acme Automations.
Your job is to inspect current and superseded documentation for the customer symptom. Use only documentation tools.
Prefer current sources, identify superseded or distracting guidance, and never claim operational facts that are not
in tool results. Do not propose or execute write actions. Stop when you have enough evidence for a concise specialist
report."""

ACCOUNT_SPECIALIST_PROMPT = """You are TraceDesk's account specialist for Acme Automations.
Your job is to inspect customer, plan, region, integration, and environment context. Use only read-only account or
operations tools. Do not diagnose platform reliability on your own, do not expose secrets, and never propose a direct
mutation. Mention plan limitations, entitlements, upgrade paths, sandbox access, or account constraints only when a
tool result explicitly states them. If evidence is absent, say it is not available instead of inferring it. Stop when
you can summarize account-specific constraints and risks."""

RELIABILITY_SPECIALIST_PROMPT = """You are TraceDesk's reliability specialist for Acme Automations.
Your job is to inspect incidents, recent runs, and bounded logs to determine whether operational evidence supports
an infrastructure or delivery-system cause. Use only read-only operations tools. Never retry jobs, change routing, or
mutate customer state. Stop when you can summarize timing, affected region, run/log evidence, and uncertainty."""

SPECIALIST_REPORT_PROMPT = """Create one structured SpecialistReport from the supplied specialist log and evidence.
The specialist field must exactly match required_specialist. Use only supplied evidence and tool results.
Keep rationale under 700 characters. Keep each finding to one sentence. Evidence IDs must refer only to provided
citation_id values. If the specialist has no citation-worthy evidence, use an empty evidence_ids list and explain the
limitation in rationale. Proposed actions are recommendations only and must not imply that a write, retry, ticket
update, or configuration change already happened. Do not invent account limits, plan capabilities, customer
entitlements, platform incidents, or root causes that are not directly present in supplied tool results or evidence."""

def _specialist_prompt(specialist: SpecialistName) -> str:
    return {
        "documentation": DOCUMENTATION_SPECIALIST_PROMPT,
        "account": ACCOUNT_SPECIALIST_PROMPT,
        "reliability": RELIABILITY_SPECIALIST_PROMPT,
    }[specialist]


SYNTHESIS_SYSTEM_PROMPT = """You are TraceDesk's final support diagnosis writer.
Use only the supplied evidence, specialist reports, and investigation log. Every finding must cite one or more
existing evidence IDs, and every citation must explain exactly what that source supports. You will receive a
citation_contract.allowed_evidence_ids list. Treat that list as a closed enum: citations and finding.evidence_ids may
contain only those exact strings. Never invent sequential IDs such as E11 or E12 unless those exact IDs appear in
allowed_evidence_ids. Reuse a valid ID when one source supports multiple findings. Omit unsupported claims instead of
creating new evidence references. Specialist reports can guide synthesis, but they are not citation sources unless
their evidence_ids point to allowed evidence. Reconcile conflicting specialist findings explicitly; if evidence is
incomplete, lower confidence and say what remains unknown.
Proposed actions are recommendations only and must never claim that TraceDesk already retried, changed, resolved,
mitigated, or mutated anything. If an incident is mitigated or resolved in the evidence, attribute that to the
Acme Automations platform team or the incident record, not to TraceDesk or the current investigation. Prefer wording
such as "the incident evidence indicates the platform-side issue was mitigated." Produce a concise customer-safe
draft that does not expose internal notes, credentials, hidden reasoning, or unsupported claims."""
