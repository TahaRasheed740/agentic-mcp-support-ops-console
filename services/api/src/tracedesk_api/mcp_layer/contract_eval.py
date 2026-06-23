from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, insert

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine
from tracedesk_api.mcp_layer.contracts import AuthorizationContext
from tracedesk_api.mcp_layer.gateway import MCPGateway, MCPGatewayError
from tracedesk_api.models import DemoSession


async def evaluate_contracts() -> dict[str, Any]:
    gateway = MCPGateway()
    session_id = str(uuid4())
    engine = create_engine(get_settings())
    async with engine.begin() as connection:
        await connection.execute(
            insert(DemoSession).values(
                id=session_id,
                persona_id="persona_maya",
                created_at=datetime.now(UTC),
                reset_at=None,
            )
        )
    authorization = AuthorizationContext(
        request_id=f"contract_{uuid4().hex}",
        persona_id="persona_maya",
        session_id=session_id,
        scopes=["knowledge:read", "operations:read", "support:read", "support:write"],
        approved_action_ids=["contract-approval"],
    )
    checks: dict[str, bool] = {}
    try:
        catalog = await gateway.catalog()
        expected_tools = {
            "knowledge": {"search_knowledge", "get_document"},
            "operations": {"get_integration", "list_recent_runs", "get_run_logs", "list_incidents"},
            "support": {"list_cases", "get_case", "update_ticket_status", "add_internal_note"},
        }
        checks["transport_and_initialize"] = len(catalog.servers) == 3
        checks["tool_contracts"] = all(
            {tool.name for tool in server.tools} == expected_tools[server.name]
            and all("authorization" in tool.input_schema.get("properties", {}) for tool in server.tools)
            for server in catalog.servers
        )
        checks["resources"] = all(len(server.resources) == 1 for server in catalog.servers)
        checks["prompts"] = all(len(server.prompts) == 1 for server in catalog.servers)

        knowledge = await gateway.call_tool(
            "knowledge",
            "search_knowledge",
            {"query": "webhook 401 after secret rotation", "limit": 3, "mode": "hybrid"},
            authorization,
        )
        operations = await gateway.call_tool(
            "operations",
            "list_incidents",
            {"region": "eu-west", "limit": 3},
            authorization,
        )
        support = await gateway.call_tool(
            "support", "get_case", {"case_id": "TKT-1007"}, authorization
        )
        checks["read_tools"] = bool(
            knowledge["data"] and operations["data"] and support["data"]
        )

        unauthorized = authorization.model_copy(update={"scopes": []})
        try:
            await gateway.call_tool(
                "support", "get_case", {"case_id": "TKT-1007"}, unauthorized
            )
        except MCPGatewayError:
            checks["authorization_denied"] = True
        else:
            checks["authorization_denied"] = False

        unapproved = authorization.model_copy(update={"approved_action_ids": []})
        write_arguments = {
            "case_id": "TKT-1007",
            "status": "investigating",
            "approval_id": "contract-approval",
            "idempotency_key": f"contract-{uuid4().hex}",
        }
        try:
            await gateway.call_tool(
                "support", "update_ticket_status", write_arguments, unapproved
            )
        except MCPGatewayError:
            checks["approval_required"] = True
        else:
            checks["approval_required"] = False

        first_write = await gateway.call_tool(
            "support", "update_ticket_status", write_arguments, authorization
        )
        replay_write = await gateway.call_tool(
            "support", "update_ticket_status", write_arguments, authorization
        )
        checks["idempotent_write"] = (
            first_write["meta"]["idempotent_replay"] is False
            and replay_write["meta"]["idempotent_replay"] is True
        )
        conflicting_arguments = {**write_arguments, "status": "resolved"}
        try:
            await gateway.call_tool(
                "support", "update_ticket_status", conflicting_arguments, authorization
            )
        except MCPGatewayError:
            checks["idempotency_conflict"] = True
        else:
            checks["idempotency_conflict"] = False

        try:
            await gateway.call_tool(
                "knowledge", "get_document", {"document_id": "missing-source"}, authorization
            )
        except MCPGatewayError:
            checks["typed_failure"] = True
        else:
            checks["typed_failure"] = False

        timeout_gateway = MCPGateway(
            get_settings().model_copy(update={"mcp_timeout_seconds": 0.000001})
        )
        try:
            await timeout_gateway.call_tool(
                "support", "get_case", {"case_id": "TKT-1007"}, authorization
            )
        except MCPGatewayError as error:
            checks["timeout_boundary"] = "timed out" in str(error)
        else:
            checks["timeout_boundary"] = False
    finally:
        async with engine.begin() as connection:
            await connection.execute(delete(DemoSession).where(DemoSession.id == session_id))
        await engine.dispose()
    return {"passed": all(checks.values()), "checks": checks}


async def main() -> None:
    report = await evaluate_contracts()
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
