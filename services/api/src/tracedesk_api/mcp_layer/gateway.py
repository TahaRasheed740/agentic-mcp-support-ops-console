from __future__ import annotations

import asyncio
import json
from typing import Any, cast

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from tracedesk_api.config import Settings, get_settings
from tracedesk_api.mcp_layer.contracts import (
    AuthorizationContext,
    ExplorerCatalog,
    ExplorerPrompt,
    ExplorerResource,
    ExplorerServer,
    ExplorerTool,
    ServiceName,
)


class MCPGatewayError(RuntimeError):
    pass


class MCPGateway:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def call_tool(
        self,
        service: ServiceName,
        tool: str,
        arguments: dict[str, Any],
        authorization: AuthorizationContext,
    ) -> dict[str, Any]:
        supplied = {key: value for key, value in arguments.items() if key != "authorization"}
        supplied["authorization"] = authorization.model_dump(mode="json")
        try:
            async with asyncio.timeout(self.settings.mcp_timeout_seconds):
                async with streamable_http_client(self._url(service)) as streams:
                    read_stream, write_stream, _ = streams
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(tool, arguments=supplied)
        except TimeoutError as error:
            raise MCPGatewayError(f"{service}.{tool} timed out") from error
        except Exception as error:
            raise MCPGatewayError(f"{service}.{tool} failed: {error}") from error
        if result.isError:
            message = "MCP tool returned an error"
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    message = str(text)
                    break
            raise MCPGatewayError(message)
        structured = getattr(result, "structuredContent", None)
        if structured is None:
            structured = getattr(result, "structured_content", None)
        if isinstance(structured, dict):
            return cast(dict[str, Any], structured)
        for block in result.content:
            text = getattr(block, "text", None)
            if text:
                parsed = json.loads(str(text))
                if isinstance(parsed, dict):
                    return cast(dict[str, Any], parsed)
        raise MCPGatewayError(f"{service}.{tool} returned no structured result")

    async def catalog(self) -> ExplorerCatalog:
        servers = await asyncio.gather(*(self._inspect(service) for service in _SERVICES))
        return ExplorerCatalog(servers=list(servers))

    async def _inspect(self, service: ServiceName) -> ExplorerServer:
        try:
            async with asyncio.timeout(self.settings.mcp_timeout_seconds):
                async with streamable_http_client(self._url(service)) as streams:
                    read_stream, write_stream, _ = streams
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tools, resources, prompts = await asyncio.gather(
                            session.list_tools(),
                            session.list_resources(),
                            session.list_prompts(),
                        )
        except Exception as error:
            raise MCPGatewayError(f"Unable to inspect {service} MCP service: {error}") from error
        return ExplorerServer(
            name=service,
            tools=[
                ExplorerTool(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                    output_schema=getattr(tool, "outputSchema", None),
                )
                for tool in tools.tools
            ],
            resources=[
                ExplorerResource(
                    uri=str(resource.uri),
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mimeType,
                )
                for resource in resources.resources
            ],
            prompts=[
                ExplorerPrompt(name=prompt.name, description=prompt.description)
                for prompt in prompts.prompts
            ],
        )

    def _url(self, service: ServiceName) -> str:
        return {
            "knowledge": self.settings.knowledge_mcp_url,
            "operations": self.settings.operations_mcp_url,
            "support": self.settings.support_mcp_url,
        }[service]


_SERVICES: tuple[ServiceName, ...] = ("knowledge", "operations", "support")
