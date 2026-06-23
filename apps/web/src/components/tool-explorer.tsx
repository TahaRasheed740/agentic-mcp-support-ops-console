"use client";

import { useMemo, useState } from "react";
import type { MCPServer } from "@/lib/api";
import { titleCase } from "@/lib/api";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const examples: Record<string, Record<string, unknown>> = {
  search_knowledge: { query: "webhook 401 after secret rotation", limit: 3, mode: "hybrid" },
  get_document: { document_id: "webhook-authentication" },
  get_integration: { integration_id: "int_0001" },
  list_recent_runs: { integration_id: "int_0001", limit: 5 },
  get_run_logs: { run_id: "run_00001", limit: 10 },
  list_incidents: { region: "eu-west", limit: 3 },
  list_cases: { page: 1, page_size: 5 },
  get_case: { case_id: "TKT-1007" },
  update_ticket_status: {
    case_id: "TKT-1007",
    status: "investigating",
    approval_id: "approval-required",
    idempotency_key: "demo-status-1007",
  },
  add_internal_note: {
    case_id: "TKT-1007",
    note: "Customer impact verified against the regional incident.",
    approval_id: "approval-required",
    idempotency_key: "demo-note-1007",
  },
};

export function ToolExplorer({ servers }: { servers: MCPServer[] }) {
  const [serverName, setServerName] = useState(servers[0]?.name ?? "knowledge");
  const server = servers.find((candidate) => candidate.name === serverName) ?? servers[0];
  const [selectedByServer, setSelectedByServer] = useState<Record<string, string>>({});
  const toolName = selectedByServer[server.name] ?? server.tools[0]?.name ?? "";
  const tool = server.tools.find((candidate) => candidate.name === toolName) ?? server.tools[0];
  const defaultArguments = useMemo(() => JSON.stringify(examples[tool?.name] ?? {}, null, 2), [tool?.name]);
  const [editedArguments, setEditedArguments] = useState<Record<string, string>>({});
  const argumentText = editedArguments[tool?.name] ?? defaultArguments;
  const [result, setResult] = useState<string>("Select a tool and run it to inspect its typed response.");
  const [running, setRunning] = useState(false);

  async function runTool() {
    setRunning(true);
    try {
      const argumentsValue = JSON.parse(argumentText) as Record<string, unknown>;
      const response = await fetch(`${apiUrl}/api/v1/mcp/${server.name}/tools/${tool.name}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arguments: argumentsValue }),
      });
      const body = (await response.json()) as unknown;
      setResult(JSON.stringify(body, null, 2));
    } catch (error) {
      setResult(JSON.stringify({ error: error instanceof Error ? error.message : "Tool call failed" }, null, 2));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="tool-explorer">
      <div className="server-tabs" role="tablist" aria-label="MCP services">
        {servers.map((candidate) => (
          <button
            aria-selected={candidate.name === server.name}
            className={candidate.name === server.name ? "active" : ""}
            key={candidate.name}
            onClick={() => setServerName(candidate.name)}
            role="tab"
            type="button"
          >
            <span>{candidate.tools.length} tools</span>
            {titleCase(candidate.name)}
          </button>
        ))}
      </div>

      <section className="tool-workspace">
        <div className="tool-control-panel">
          <label htmlFor="tool-select">Tool</label>
          <select
            id="tool-select"
            onChange={(event) => setSelectedByServer((current) => ({ ...current, [server.name]: event.target.value }))}
            value={tool.name}
          >
            {server.tools.map((candidate) => <option key={candidate.name}>{candidate.name}</option>)}
          </select>
          <p>{tool.description}</p>
          <div className="contract-label">
            <span>Input contract</span>
            {tool.name === "update_ticket_status" || tool.name === "add_internal_note" ? <strong>Approval gated</strong> : <strong>Read only</strong>}
          </div>
          <pre className="schema-view">{JSON.stringify(tool.input_schema, null, 2)}</pre>
          <label htmlFor="tool-arguments">Arguments</label>
          <textarea
            id="tool-arguments"
            onChange={(event) => setEditedArguments((current) => ({ ...current, [tool.name]: event.target.value }))}
            spellCheck={false}
            value={argumentText}
          />
          <button className="run-tool" disabled={running} onClick={runTool} type="button">
            {running ? "Calling service..." : "Run tool"}
          </button>
        </div>
        <div className="tool-result-panel">
          <span>Structured response</span>
          <pre>{result}</pre>
          <div className="capability-list">
            <div><strong>{server.resources.length} resources</strong>{server.resources.map((resource) => <code key={resource.uri}>{resource.uri}</code>)}</div>
            <div><strong>{server.prompts.length} prompts</strong>{server.prompts.map((prompt) => <code key={prompt.name}>{prompt.name}</code>)}</div>
          </div>
        </div>
      </section>
    </div>
  );
}
