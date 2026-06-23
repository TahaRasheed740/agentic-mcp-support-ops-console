"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { Investigation, InvestigationEvent, ProposedAction } from "@/lib/api";
import { titleCase } from "@/lib/api";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const eventTypes = [
  "investigation.created", "investigation.started", "classification.completed", "plan.completed",
  "agent.started", "tool.requested", "tool.completed", "evidence.added", "model.text_delta",
  "budget.updated", "retry.scheduled", "specialist.started", "specialist.completed", "specialist.reconciled",
  "action.proposed", "action.approved", "action.rejected", "action.executed", "action.failed", "action.stale",
  "diagnosis.completed", "investigation.completed", "investigation.failed",
];

export function InvestigationWorkspace({
  initial,
  initialEvents = [],
  mode = "live",
  replaySummary,
}: {
  initial: Investigation;
  initialEvents?: InvestigationEvent[];
  mode?: "live" | "replay";
  replaySummary?: string;
}) {
  const [view, setView] = useState(initial);
  const [events, setEvents] = useState<InvestigationEvent[]>(initialEvents);
  const [connection, setConnection] = useState<"connecting" | "live" | "closed">(
    mode === "replay" ? "closed" : "connecting",
  );
  const [actionBusy, setActionBusy] = useState<string | null>(null);

  useEffect(() => {
    if (mode === "replay") return;
    const source = new EventSource(`${apiUrl}/api/v1/investigations/${view.id}/events`, { withCredentials: true });
    source.onopen = () => setConnection("live");
    source.onerror = () => setConnection("connecting");
    for (const eventType of eventTypes) {
      source.addEventListener(eventType, (raw) => {
        const event = JSON.parse((raw as MessageEvent<string>).data) as InvestigationEvent;
        setEvents((current) => current.some((item) => item.sequence === event.sequence) ? current : [...current, event]);
        applyEvent(event, setView);
        if (event.event_type === "investigation.completed" || event.event_type === "investigation.failed") {
          void refresh(view.id, setView);
          setConnection("closed");
          source.close();
        }
      });
    }
    return () => source.close();
  }, [mode, view.id]);

  const agentNotes = useMemo(
    () => buildAgentNotes(events),
    [events],
  );

  return (
    <div className="investigation-grid">
      <section className="investigation-main">
        <div className="investigation-hero panel">
          <div>
            <span className="panel-label">{mode === "replay" ? "Recorded replay" : "Live Claude investigation"}</span>
            <h1>{view.case_id}</h1>
            <p>{replaySummary ?? view.classification?.summary ?? "Classification is starting."}</p>
          </div>
          <div className="investigation-state">
            <span className={`connection-dot ${connection}`} />{mode === "replay" ? "Replay" : connection === "live" ? "Streaming" : titleCase(view.status)}
          </div>
        </div>
        {mode === "replay" && (
          <div className="replay-banner" role="note">
            This is a frozen anonymous replay. It does not call Claude, stream SSE, or mutate support state.
          </div>
        )}

        <div className="investigation-metrics">
          <Metric label="Tool calls" value={`${view.tool_calls} / 30`} />
          <Metric label="Input tokens" value={view.input_tokens.toLocaleString()} />
          <Metric label="Output tokens" value={view.output_tokens.toLocaleString()} />
          <Metric label="Evidence" value={String(view.evidence.length)} />
        </div>

        {view.error && <div className="investigation-error" role="alert"><strong>Investigation failed</strong><p>{view.error}</p></div>}
        {mode === "live" && (
          <Link className="return-link" href={`/cases/${view.case_id}`}>
            Return to case detail
          </Link>
        )}

        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Agent activity</span><h2>Investigation timeline</h2></div><span>{events.length} events</span></div>
          {agentNotes.length > 0 && (
            <div className="agent-note-grid">
              {agentNotes.map((note) => (
                <article className="agent-note" key={note.agent}>
                  <span>{agentLabel(note.agent)}</span>
                  <p>{note.text}</p>
                </article>
              ))}
            </div>
          )}
          <div className="event-list">
            {events.filter((event) => event.event_type !== "model.text_delta").map((event) => <EventRow event={event} key={event.sequence} />)}
            {!events.length && <p className="muted-copy">Waiting for the first persisted event...</p>}
          </div>
        </section>

        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Parallel specialists</span><h2>Specialist reports</h2></div><span>{view.specialist_reports.length}</span></div>
          <div className="specialist-grid">
            {view.specialist_reports.map((report) => (
              <article className="specialist-card" key={report.specialist}>
                <span>{titleCase(report.specialist)}</span>
                <strong>{titleCase(report.status)}</strong>
                <p>{report.rationale}</p>
                {report.findings.map((finding) => <small key={finding}>{finding}</small>)}
              </article>
            ))}
            {!view.specialist_reports.length && <p className="muted-copy">Specialists have not reported yet.</p>}
          </div>
        </section>

        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Human approval required</span><h2>Action queue</h2></div><span>{view.proposed_actions.length}</span></div>
          <div className="action-list">
            {view.proposed_actions.map((action) => (
              <ActionCard
                action={action}
                busy={actionBusy === action.id}
                key={action.id}
                mode={mode}
                onDecision={(decision) => decideAction(view.id, action.id, decision, setView, setActionBusy)}
              />
            ))}
            {!view.proposed_actions.length && <p className="muted-copy">No state-changing actions have been proposed.</p>}
          </div>
        </section>

        {view.diagnosis && (
          <section className="panel diagnosis-panel">
            <div className="panel-heading"><div><span>Evidence-grounded result</span><h2>Diagnosis</h2></div><span className={`confidence ${view.diagnosis.confidence}`}>{view.diagnosis.confidence} confidence</span></div>
            <div className="diagnosis-body">
              <p className="diagnosis-summary">{view.diagnosis.summary}</p>
              <h3>Root cause</h3><p>{view.diagnosis.root_cause}</p>
              <h3>Findings</h3>
              {view.diagnosis.findings.map((finding) => <p className="finding" key={finding.claim}>{finding.claim} <CitationLinks ids={finding.evidence_ids} /></p>)}
              <h3>Drafted customer response</h3><div className="draft-response">{view.diagnosis.drafted_response}</div>
            </div>
          </section>
        )}
      </section>

      <aside className="investigation-side">
        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Router</span><h2>Classification</h2></div></div>
          {view.classification ? <div className="classification-card"><strong>{titleCase(view.classification.category)}</strong><span>{titleCase(view.classification.urgency)} / {titleCase(view.classification.complexity)}</span><p>{view.classification.rationale}</p></div> : <p className="muted-copy">Pending...</p>}
        </section>
        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Workflow</span><h2>Plan</h2></div></div>
          {view.plan ? <ol className="plan-list">{view.plan.steps.map((step) => <li key={step}>{step}</li>)}</ol> : <p className="muted-copy">Pending...</p>}
        </section>
        <section className="panel investigation-section">
          <div className="panel-heading"><div><span>Sources</span><h2>Evidence</h2></div><span>{view.evidence.length}</span></div>
          <div className="captured-evidence">
            {view.evidence.map((item) => (
              <article id={`citation-${item.citation_id}`} key={item.citation_id} tabIndex={-1}>
                <span>{item.citation_id}</span>
                <strong>{item.title}</strong>
                <code>{item.document_id}</code>
                <p>{item.excerpt.slice(0, 190)}{item.excerpt.length > 190 ? "..." : ""}</p>
                <Link href={`/knowledge?q=${encodeURIComponent(item.document_id)}`}>Inspect source</Link>
              </article>
            ))}
            {!view.evidence.length && (
              <p className="muted-copy">
                No evidence captured yet. If the model or MCP service times out, the failed event will appear in the timeline.
              </p>
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}

function applyEvent(event: InvestigationEvent, setView: React.Dispatch<React.SetStateAction<Investigation>>) {
  setView((current) => {
    if (event.event_type === "investigation.started") return { ...current, status: "running" };
    if (event.event_type === "classification.completed") return { ...current, classification: event.payload as Investigation["classification"] };
    if (event.event_type === "plan.completed") return { ...current, plan: event.payload as Investigation["plan"] };
    if (event.event_type === "evidence.added") return { ...current, evidence: current.evidence.some((item) => item.citation_id === event.payload.citation_id) ? current.evidence : [...current.evidence, event.payload as Investigation["evidence"][number]] };
    if (event.event_type === "budget.updated") return { ...current, input_tokens: Number(event.payload.input_tokens), output_tokens: Number(event.payload.output_tokens), cache_read_tokens: Number(event.payload.cache_read_tokens), cache_creation_tokens: Number(event.payload.cache_creation_tokens), tool_calls: Number(event.payload.tool_calls) };
    if (event.event_type === "specialist.completed") return { ...current, specialist_reports: current.specialist_reports.some((item) => item.specialist === event.payload.specialist) ? current.specialist_reports : [...current.specialist_reports, event.payload as Investigation["specialist_reports"][number]] };
    if (event.event_type.startsWith("action.")) {
      const action = event.payload as Investigation["proposed_actions"][number];
      if (!action.id) return current;
      const exists = current.proposed_actions.some((item) => item.id === action.id);
      return { ...current, proposed_actions: exists ? current.proposed_actions.map((item) => item.id === action.id ? action : item) : [...current.proposed_actions, action] };
    }
    if (event.event_type === "diagnosis.completed") return { ...current, diagnosis: event.payload as Investigation["diagnosis"], drafted_response: String(event.payload.drafted_response ?? "") };
    if (event.event_type === "investigation.completed") return { ...current, status: "completed" };
    if (event.event_type === "investigation.failed") return { ...current, status: "failed", error: String(event.payload.message ?? "Investigation failed") };
    return current;
  });
}

async function decideAction(
  investigationId: string,
  actionId: string,
  decision: "approve" | "reject",
  setView: React.Dispatch<React.SetStateAction<Investigation>>,
  setActionBusy: React.Dispatch<React.SetStateAction<string | null>>,
) {
  setActionBusy(actionId);
  const endpoint = `${apiUrl}/api/v1/investigations/${investigationId}/actions/${actionId}/${decision}`;
  const response = await fetch(endpoint, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: decision === "reject" ? JSON.stringify({ reason: "Rejected in TraceDesk review" }) : undefined,
  });
  if (response.ok) {
    const action = (await response.json()) as ProposedAction;
    setView((current) => ({
      ...current,
      proposed_actions: current.proposed_actions.map((item) => item.id === action.id ? action : item),
    }));
  }
  setActionBusy(null);
}

async function refresh(id: string, setView: React.Dispatch<React.SetStateAction<Investigation>>) {
  const response = await fetch(`${apiUrl}/api/v1/investigations/${id}`, { credentials: "include" });
  if (response.ok) setView((await response.json()) as Investigation);
}

function EventRow({ event }: { event: InvestigationEvent }) {
  const summary = eventSummary(event);
  return <div className="event-row"><span>{String(event.sequence).padStart(2, "0")}</span><div><strong>{summary.label}</strong>{summary.detail && <small>{summary.detail}</small>}</div><code>{agentLabel(event.agent)}</code></div>;
}

function buildAgentNotes(events: InvestigationEvent[]) {
  const notes = new Map<string, string>();
  for (const event of events) {
    if (event.event_type !== "model.text_delta") continue;
    const text = payloadString(event.payload, "text").replace(/\s+/g, " ").trim();
    if (!text) continue;
    notes.set(event.agent, `${notes.get(event.agent) ?? ""}${text} `);
  }
  return Array.from(notes, ([agent, text]) => ({
    agent,
    text: compactActivityText(text.trim()),
  }));
}

function compactActivityText(text: string) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) ?? [text];
  const cleaned = sentences
    .map((sentence) => sentence.trim())
    .filter((sentence, index, all) => all.indexOf(sentence) === index)
    .slice(-4)
    .join(" ");
  return cleaned.length > 520 ? `${cleaned.slice(0, 500).trim()}...` : cleaned;
}

function eventSummary(event: InvestigationEvent) {
  const agent = agentLabel(event.agent);
  if (event.event_type === "investigation.started") return { label: "Investigation started", detail: "" };
  if (event.event_type === "classification.completed") return { label: "Router classified the case", detail: `${payloadString(event.payload, "category")} / ${payloadString(event.payload, "urgency")}` };
  if (event.event_type === "plan.completed") return { label: "Router created an investigation plan", detail: "" };
  if (event.event_type === "agent.started") return { label: "General investigator started", detail: payloadList(event.payload, "allowed_tools").join(", ") };
  if (event.event_type === "specialist.started") return { label: `${agent} started`, detail: "Bounded read-only specialist lane" };
  if (event.event_type === "specialist.completed") return { label: `${agent} completed report`, detail: payloadString(event.payload, "rationale") };
  if (event.event_type === "specialist.reconciled") return { label: "Specialist findings reconciled", detail: payloadList(event.payload, "specialists").map(agentLabel).join(", ") };
  if (event.event_type === "tool.requested") return { label: `${agent} called ${payloadString(event.payload, "tool")}`, detail: `${payloadString(event.payload, "service")}.${payloadString(event.payload, "tool")}` };
  if (event.event_type === "tool.completed") return { label: `${payloadString(event.payload, "tool")} returned`, detail: `${agent} received MCP result` };
  if (event.event_type === "evidence.added") return { label: `Captured ${payloadString(event.payload, "citation_id")}`, detail: payloadString(event.payload, "title") };
  if (event.event_type === "budget.updated") return { label: "Budget updated", detail: `${payloadString(event.payload, "tool_calls")} tool calls` };
  if (event.event_type === "retry.scheduled") return { label: "Model retry scheduled", detail: `Attempt ${payloadString(event.payload, "attempt")} in ${payloadString(event.payload, "delay_seconds")}s` };
  if (event.event_type === "action.proposed") return { label: "Approval action proposed", detail: payloadString(event.payload, "title") };
  if (event.event_type === "diagnosis.completed") return { label: "Diagnosis drafted", detail: payloadString(event.payload, "confidence") };
  if (event.event_type === "investigation.completed") return { label: "Investigation completed", detail: "" };
  if (event.event_type === "investigation.failed") return { label: "Investigation failed", detail: payloadString(event.payload, "message") };
  return { label: event.event_type.split(".").map(titleCase).join(" / "), detail: "" };
}

function payloadString(payload: Record<string, unknown>, key: string) {
  const value = payload[key];
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function payloadList(payload: Record<string, unknown>, key: string) {
  const value = payload[key];
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item));
}

function agentLabel(agent: string) {
  return agent.split(/[_\s-]+/).filter(Boolean).map(titleCase).join(" ");
}

function CitationLinks({ ids }: { ids: string[] }) {
  return (
    <span className="citation-links">
      {ids.map((id) => (
        <button
          aria-label={`Show evidence ${id}`}
          key={id}
          onClick={() => scrollToEvidence(id)}
          type="button"
        >
          [{id}]
        </button>
      ))}
    </span>
  );
}

function scrollToEvidence(id: string) {
  const target = document.getElementById(`citation-${id}`);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.focus({ preventScroll: true });
  target.classList.add("evidence-target");
  window.setTimeout(() => target.classList.remove("evidence-target"), 1600);
}

function ActionCard({
  action,
  busy,
  mode,
  onDecision,
}: {
  action: ProposedAction;
  busy: boolean;
  mode: "live" | "replay";
  onDecision: (decision: "approve" | "reject") => void;
}) {
  const pending = action.status === "pending";
  return (
    <article className={`action-card ${action.status}`}>
      <div>
        <span>{titleCase(action.action_type)}</span>
        <strong>{action.title}</strong>
        <p>{action.rationale}</p>
        <code>{action.service}.{action.tool_name}</code>
        {action.error && <small>{action.error}</small>}
      </div>
      <div className="action-controls">
        <span className={`status-badge ${action.status}`}>{titleCase(action.status)}</span>
        {pending && mode === "live" && <button disabled={busy} onClick={() => onDecision("approve")}>{busy ? "Working..." : "Approve"}</button>}
        {pending && mode === "live" && <button disabled={busy} onClick={() => onDecision("reject")}>Reject</button>}
        {pending && mode === "replay" && <small>Replay only: approvals are disabled.</small>}
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value}</strong></div>;
}
