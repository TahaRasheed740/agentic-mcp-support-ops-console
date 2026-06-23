from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ServiceName = Literal["knowledge", "operations", "support"]


class AuthorizationContext(BaseModel):
    request_id: str = Field(min_length=8, max_length=80)
    persona_id: str = Field(min_length=3, max_length=40)
    session_id: str | None = Field(default=None, min_length=8, max_length=80)
    scopes: list[str] = Field(default_factory=list, max_length=20)
    approved_action_ids: list[str] = Field(default_factory=list, max_length=20)


class ToolMeta(BaseModel):
    service: ServiceName
    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    idempotent_replay: bool = False


class ToolResponse(BaseModel):
    ok: bool = True
    data: dict[str, Any] | list[Any]
    meta: ToolMeta


class ToolFailure(BaseModel):
    ok: Literal[False] = False
    code: Literal[
        "authorization_denied",
        "approval_required",
        "conflict",
        "invalid_request",
        "not_found",
        "timeout",
        "upstream_failure",
    ]
    message: str
    retryable: bool = False
    meta: ToolMeta


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class ExplorerTool(BaseModel):
    name: str
    description: str | None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None


class ExplorerResource(BaseModel):
    uri: str
    name: str
    description: str | None
    mime_type: str | None


class ExplorerPrompt(BaseModel):
    name: str
    description: str | None


class ExplorerServer(BaseModel):
    name: ServiceName
    tools: list[ExplorerTool]
    resources: list[ExplorerResource]
    prompts: list[ExplorerPrompt]


class ExplorerCatalog(BaseModel):
    servers: list[ExplorerServer]


class ExplorerCallResponse(BaseModel):
    server: ServiceName
    tool: str
    result: dict[str, Any]
