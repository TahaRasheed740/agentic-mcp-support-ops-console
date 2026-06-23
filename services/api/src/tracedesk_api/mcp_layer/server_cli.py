from __future__ import annotations

import argparse

from tracedesk_api.mcp_layer.contracts import ServiceName


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one TraceDesk MCP service")
    parser.add_argument("service", choices=("knowledge", "operations", "support"))
    args = parser.parse_args()
    run_server(args.service)


def run_server(service: ServiceName) -> None:
    if service == "knowledge":
        from tracedesk_api.mcp_layer.knowledge_server import knowledge_mcp

        server = knowledge_mcp
    elif service == "operations":
        from tracedesk_api.mcp_layer.operations_server import operations_mcp

        server = operations_mcp
    else:
        from tracedesk_api.mcp_layer.support_server import support_mcp

        server = support_mcp
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
