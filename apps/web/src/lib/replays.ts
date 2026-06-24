import type { Diagnosis, Investigation, InvestigationEvent, InvestigationPlan, ProposedAction, SpecialistReport } from "@/lib/api";

export type ReplayScenario = {
  id: string;
  title: string;
  summary: string;
  caseId: string;
  duration: string;
  tags: string[];
  investigation: Investigation;
  events: InvestigationEvent[];
};

type Evidence = Investigation["evidence"][number];
type Classification = NonNullable<Investigation["classification"]>;

type ScenarioSeed = {
  id: string;
  title: string;
  summary: string;
  caseId: string;
  tags: string[];
  classification: Classification;
  plan: InvestigationPlan;
  evidence: Evidence[];
  specialists: SpecialistReport[];
  diagnosis: Diagnosis;
  action: ProposedAction | null;
  usage: { input_tokens: number; output_tokens: number; cache_creation_tokens: number; tool_calls: number };
  toolFlow: Array<{ agent: string; service: string; tool: string; detail: string }>;
  agentNotes: Array<{ agent: string; text: string }>;
};

const completedAt = "2026-06-14T12:48:00.000Z";

export const replayScenarios: ReplayScenario[] = [
  createScenario({
    id: "eu-webhook-latency",
    title: "EU Webhook Latency",
    summary:
      "Watch the agent separate a regional queue incident from a customer endpoint problem, then draft no-action guidance.",
    caseId: "TKT-1007",
    tags: ["Reliability", "Incidents", "Approval queue"],
    classification: {
      category: "reliability",
      urgency: "urgent",
      complexity: "complex",
      summary: "EU webhook delivery latency increased while US deliveries and endpoint acknowledgements stayed healthy.",
      rationale:
        "The symptom is production-impacting, region-specific, and requires correlating documentation, account context, and incident evidence.",
    },
    plan: {
      hypotheses: [
        "A regional queue backlog delayed dispatch before webhook execution.",
        "Customer endpoint latency is a distractor because acknowledgements stayed normal.",
      ],
      evidence_needed: ["Regional latency guidance", "Matching incident record", "Recent run timing"],
      allowed_tools: ["search_knowledge", "get_integration", "list_recent_runs", "list_incidents"],
      steps: [
        "Classify the issue and route reliability specialists.",
        "Search current documentation and incident evidence.",
        "Inspect integration and recent run context.",
        "Reconcile findings and draft a customer-safe response.",
      ],
    },
    evidence: [
      evidence("E1", "eu-latency-incident-review", "Incident review - EU delivery latency", "output/pdf/acme-incident-review-eu-latency.pdf", "A worker queue imbalance in eu-west increased webhook queue time for 47 minutes. Payload execution time and customer endpoint response time remained normal. No customer configuration change was required."),
      evidence("E2", "regional-delivery-latency", "Investigating region-specific delivery latency", "knowledge/docs/regional-delivery-latency.md", "Latency isolated to one region with healthy destinations should be correlated with the regional incident timeline before changing customer configuration."),
      evidence("E3", "recent-run-summary", "Recent run timing summary", "simulated operations MCP", "run_00067 completed in 1.8 seconds after the incident window, while earlier affected runs showed elevated queue timing."),
    ],
    specialists: [
      specialist("documentation", "Searched current support documentation and incident PDFs for the exact regional latency symptom.", ["Current guidance warns against customer endpoint changes when queue delay is region-specific.", "The incident review matches eu-west, webhook delivery, and queue-delay symptoms."], ["E1", "E2"]),
      specialist("account", "Checked account and integration context before proposing any support-state mutation.", ["Summit Labs is on the Scale plan in eu-west.", "The production webhook integration remains connected."], []),
      specialist("reliability", "Correlated incident timing with recent run behavior without retrying or changing jobs.", ["INC-001 describes a 47-minute eu-west queue imbalance.", "Recent runs show recovery to baseline after the incident window."], ["E1", "E3"]),
    ],
    diagnosis: diagnosis(
      "Summit Labs experienced elevated EU webhook delivery latency that matches incident INC-001.",
      "A worker queue imbalance in eu-west delayed dispatch. The platform-side issue was mitigated by the Acme Automations platform team.",
      ["The incident review describes a eu-west worker queue imbalance that delayed webhook dispatch without data loss.", "Current guidance supports avoiding endpoint or secret changes.", "Recent run context shows the latest run returned to normal latency."],
      ["E1", "E2", "E3"],
      "We found that your EU webhook deliveries were delayed by a regional Acme Automations queue issue, not by your endpoint. Deliveries were delayed rather than lost, and no customer-side action is recommended.",
    ),
    action: action("replay-action-eu-note", "TKT-1007", "Add consolidated investigation note", "Record the incident correlation, recovery signal, and no-customer-action guidance.", ["E1", "E2", "E3"]),
    usage: { input_tokens: 2330, output_tokens: 546, cache_creation_tokens: 2027, tool_calls: 11 },
    toolFlow: [
      tool("documentation", "knowledge", "search_knowledge", "regional webhook latency eu-west"),
      tool("reliability", "operations", "list_incidents", "matching eu-west incident"),
      tool("reliability", "operations", "list_recent_runs", "recent webhook dispatch timing"),
      tool("account", "operations", "get_integration", "production webhook integration"),
    ],
    agentNotes: [
      { agent: "router", text: "The case is region-specific and urgent, so I am routing documentation, reliability, and account checks in parallel." },
      { agent: "reliability", text: "The timing matches the incident window, and the latest run shows latency has returned to baseline." },
      { agent: "investigator", text: "The evidence points to platform queue delay, not endpoint failure. The safest customer guidance is no retry, no endpoint change, and no secret rotation." },
    ],
  }),
  createScenario({
    id: "webhook-secret-rotation",
    title: "Webhook 401 After Secret Rotation",
    summary:
      "Watch the agent verify a credential-rotation mismatch and avoid blaming the platform or retrying blindly.",
    caseId: "TKT-1001",
    tags: ["Authentication", "RAG", "Webhook"],
    classification: {
      category: "authentication",
      urgency: "high",
      complexity: "moderate",
      summary: "Webhook deliveries began returning 401 immediately after a signing secret rotation.",
      rationale: "The timing points to a shared-secret validation mismatch rather than regional infrastructure failure.",
    },
    plan: {
      hypotheses: ["The destination still validates the previous shared secret.", "Recent retries fail because signatures are generated with the new secret."],
      evidence_needed: ["Secret rotation guidance", "Integration status", "Recent 401 run logs"],
      allowed_tools: ["search_knowledge", "get_integration", "list_recent_runs", "get_run_logs"],
      steps: ["Retrieve webhook-auth guidance.", "Inspect integration environment and rotation timing.", "Compare recent failed delivery logs.", "Draft verification and rollback-safe guidance."],
    },
    evidence: [
      evidence("E1", "webhook-authentication", "Webhook authentication failures after secret rotation", "knowledge/docs/webhook-authentication.md", "A 401 immediately after credential rotation usually means the destination still validates the previous shared secret."),
      evidence("E2", "integration-secret-state", "Integration secret rotation state", "simulated operations MCP", "The webhook integration rotated its signing secret at 09:12 UTC. Failures began on the first delivery after rotation."),
      evidence("E3", "recent-401-run-logs", "Recent 401 delivery logs", "simulated operations MCP", "Recent webhook attempts returned HTTP 401 with signature verification failed. Endpoint reachability remained healthy."),
    ],
    specialists: [
      specialist("documentation", "Pulled the current credential-rotation troubleshooting article.", ["The docs describe this exact post-rotation 401 pattern.", "Resolution requires confirming destination-side secret update before retrying."], ["E1"]),
      specialist("account", "Checked integration state and rotation timing.", ["The integration is connected and production-scoped.", "Failures started immediately after the secret rotation timestamp."], ["E2"]),
    ],
    diagnosis: diagnosis(
      "The 401 failures are consistent with the destination validating the old webhook signing secret.",
      "The Acme integration rotated its signing secret, but the customer endpoint appears to still be configured with the previous value.",
      ["Credential-rotation guidance matches the symptom.", "Integration timing lines up with the first failed delivery.", "Run logs show signature validation failure rather than endpoint outage."],
      ["E1", "E2", "E3"],
      "The evidence points to a destination-side secret mismatch after rotation. Please confirm the endpoint is using the new signing secret, then send one test delivery before retrying production traffic.",
    ),
    action: action("replay-action-auth-note", "TKT-1001", "Add rotation mismatch note", "Record the rotation timing and recommended verification workflow.", ["E1", "E2", "E3"]),
    usage: { input_tokens: 1988, output_tokens: 488, cache_creation_tokens: 1530, tool_calls: 9 },
    toolFlow: [
      tool("documentation", "knowledge", "search_knowledge", "webhook 401 secret rotation"),
      tool("account", "operations", "get_integration", "webhook signing secret state"),
      tool("investigator", "operations", "get_run_logs", "recent 401 signature failures"),
    ],
    agentNotes: [
      { agent: "router", text: "The failure starts immediately after a credential event, so authentication evidence should come first." },
      { agent: "investigator", text: "The logs show signature verification failed, while endpoint reachability stayed healthy." },
    ],
  }),
  createScenario({
    id: "stripe-schema-mapping",
    title: "Stripe Schema Mapping Change",
    summary:
      "Watch the agent trace empty email fields to a nested payload schema change and propose a safe mapping update.",
    caseId: "TKT-1005",
    tags: ["Data mapping", "Schema change", "Specialists"],
    classification: {
      category: "data_mapping",
      urgency: "high",
      complexity: "moderate",
      summary: "New Stripe events produce empty email fields after a nested customer object was introduced.",
      rationale: "Historical payloads still process correctly, so the likely issue is mapping compatibility with a changed payload shape.",
    },
    plan: {
      hypotheses: ["The email source path moved into a nested customer object.", "Existing mapping rules still target the old flat field path."],
      evidence_needed: ["Schema-change mapping docs", "Integration mapping configuration", "New versus historical run evidence"],
      allowed_tools: ["search_knowledge", "get_integration", "list_recent_runs", "get_run_logs"],
      steps: ["Search mapping schema-change guidance.", "Inspect Stripe integration mapping context.", "Compare recent and historical run behavior.", "Draft a preview-first mapping update."],
    },
    evidence: [
      evidence("E1", "mapping-schema-changes", "Handling mapping schema changes", "knowledge/docs/mapping-schema-changes.md", "When providers nest previously flat fields, existing mappings can write empty values until paths are updated and previewed."),
      evidence("E2", "stripe-mapping-config", "Stripe mapping configuration", "simulated operations MCP", "The current mapping reads customer_email from the old top-level payload path."),
      evidence("E3", "stripe-run-comparison", "New versus historical Stripe runs", "simulated operations MCP", "Historical events include customer_email at the top level. New events place email under customer.email."),
    ],
    specialists: [
      specialist("documentation", "Searched mapping and schema evolution guidance.", ["The docs warn that nested provider objects can break old field paths.", "Previewing the updated mapping is required before publishing."], ["E1"]),
      specialist("account", "Inspected the Stripe production integration and mapping configuration.", ["The integration is connected.", "The mapping still targets the old top-level email path."], ["E2"]),
    ],
    diagnosis: diagnosis(
      "The empty email fields are caused by a Stripe payload schema change that moved email into a nested customer object.",
      "The mapping rule still points to the previous top-level email path, so new events write an empty field while historical payloads continue to work.",
      ["Schema-change guidance matches the nested object symptom.", "The current mapping targets the old field path.", "Run comparison shows the old and new payload shapes diverge."],
      ["E1", "E2", "E3"],
      "The issue appears to be a mapping path mismatch after Stripe introduced a nested customer object. We should preview an updated path against affected events before publishing the mapping change.",
    ),
    action: action("replay-action-mapping-note", "TKT-1005", "Add mapping remediation note", "Document the recommended preview-first mapping update.", ["E1", "E2", "E3"]),
    usage: { input_tokens: 2214, output_tokens: 612, cache_creation_tokens: 1688, tool_calls: 10 },
    toolFlow: [
      tool("documentation", "knowledge", "search_knowledge", "stripe nested customer mapping"),
      tool("account", "operations", "get_integration", "Stripe mapping rules"),
      tool("investigator", "operations", "get_run_logs", "new versus historical Stripe payloads"),
    ],
    agentNotes: [
      { agent: "router", text: "The ticket says historical payloads still work, which makes schema compatibility more likely than an integration outage." },
      { agent: "investigator", text: "The mapping points at the old top-level email field, while new events expose email under customer.email." },
    ],
  }),
  createScenario({
    id: "salesforce-oauth-expiration",
    title: "Salesforce OAuth Expiration",
    summary:
      "Watch the agent investigate an expired Salesforce connection after reauthorization and focus on token lifecycle evidence.",
    caseId: "TKT-1018",
    tags: ["OAuth", "Account context", "Token lifecycle"],
    classification: {
      category: "authentication",
      urgency: "high",
      complexity: "moderate",
      summary: "A Salesforce OAuth connection is marked expired despite recent reauthorization attempts.",
      rationale: "The case requires account context, token lifecycle guidance, and recent retry evidence before recommending reauthorization.",
    },
    plan: {
      hypotheses: ["The refresh token was revoked or replaced during reauthorization.", "Retries continue using stale token metadata."],
      evidence_needed: ["OAuth token lifecycle guidance", "Integration token metadata", "Recent retry logs"],
      allowed_tools: ["search_knowledge", "get_integration", "list_recent_runs", "get_run_logs"],
      steps: ["Search OAuth lifecycle guidance.", "Inspect Salesforce integration status.", "Review recent retry logs.", "Draft account-safe reauthorization guidance."],
    },
    evidence: [
      evidence("E1", "oauth-token-lifecycle", "OAuth token lifecycle and refresh failures", "knowledge/docs/oauth-token-lifecycle.md", "Recent reauthorization can still fail if the provider revokes the refresh token or the integration keeps stale token metadata."),
      evidence("E2", "salesforce-token-state", "Salesforce token metadata", "simulated operations MCP", "The connection is marked expired, and the latest token refresh attempt references a revoked refresh token."),
      evidence("E3", "salesforce-retry-logs", "Salesforce retry logs", "simulated operations MCP", "Retries fail before data sync starts with provider_auth_expired. No records were partially written."),
    ],
    specialists: [
      specialist("documentation", "Retrieved OAuth lifecycle guidance for provider refresh-token failures.", ["The docs explain why recent reauthorization can still leave stale token metadata.", "The safe workflow is to reauthorize and verify a single test sync."], ["E1"]),
      specialist("account", "Checked the Salesforce production integration and token state.", ["The integration is production-scoped and marked expired.", "Refresh attempts reference a revoked token rather than a platform outage."], ["E2"]),
    ],
    diagnosis: diagnosis(
      "The Salesforce retries are failing because the integration still has expired or revoked OAuth token state.",
      "The provider refresh token appears revoked, and retries fail before sync work begins.",
      ["OAuth lifecycle guidance matches the revoked refresh-token pattern.", "Integration metadata shows expired token state.", "Retry logs fail at provider authentication before data mutation."],
      ["E1", "E2", "E3"],
      "The evidence points to OAuth token lifecycle state rather than a data sync bug. Reauthorize the Salesforce connection, then run one verification sync before resuming retries.",
    ),
    action: action("replay-action-oauth-note", "TKT-1018", "Add OAuth lifecycle note", "Record the revoked-token finding and verification workflow.", ["E1", "E2", "E3"]),
    usage: { input_tokens: 2075, output_tokens: 520, cache_creation_tokens: 1610, tool_calls: 9 },
    toolFlow: [
      tool("documentation", "knowledge", "search_knowledge", "Salesforce OAuth expired after reauthorization"),
      tool("account", "operations", "get_integration", "Salesforce token metadata"),
      tool("investigator", "operations", "get_run_logs", "provider_auth_expired retries"),
    ],
    agentNotes: [
      { agent: "router", text: "The recent reauthorization makes this a token lifecycle investigation, not a generic Salesforce outage." },
      { agent: "investigator", text: "Retries fail before sync begins, so the evidence supports an authentication-state issue rather than partial data writes." },
    ],
  }),
];

export function getReplayScenario(id: string): ReplayScenario | undefined {
  return replayScenarios.find((scenario) => scenario.id === id);
}

function createScenario(seed: ScenarioSeed): ReplayScenario {
  const investigation: Investigation = {
    id: `replay-${seed.id}`,
    case_id: seed.caseId,
    status: "completed",
    router_model: "claude-haiku-4-5",
    investigator_model: "claude-sonnet-4-5",
    classification: seed.classification,
    plan: seed.plan,
    diagnosis: seed.diagnosis,
    drafted_response: seed.diagnosis.drafted_response,
    specialist_reports: seed.specialists,
    proposed_actions: seed.action ? [seed.action] : [],
    evidence: seed.evidence,
    input_tokens: seed.usage.input_tokens,
    output_tokens: seed.usage.output_tokens,
    cache_read_tokens: 0,
    cache_creation_tokens: seed.usage.cache_creation_tokens,
    tool_calls: seed.usage.tool_calls,
    error: null,
    created_at: "2026-06-14T12:44:00.000Z",
    started_at: "2026-06-14T12:44:03.000Z",
    completed_at: completedAt,
  };
  return {
    id: seed.id,
    title: seed.title,
    summary: seed.summary,
    caseId: seed.caseId,
    duration: "3 min replay",
    tags: seed.tags,
    investigation,
    events: buildEvents(seed),
  };
}

function buildEvents(seed: ScenarioSeed): InvestigationEvent[] {
  const events: Array<Omit<InvestigationEvent, "sequence" | "timestamp">> = [];
  const push = (event_type: string, agent: string, payload: Record<string, unknown>) => {
    events.push({ event_type, agent, payload });
  };

  push("investigation.created", "workflow", { case_id: seed.caseId, status: "queued" });
  push("investigation.started", "workflow", { status: "running" });
  push("model.text_delta", "router", { text: seed.agentNotes[0]?.text ?? "Classifying the ticket and choosing a safe investigation route." });
  push("classification.completed", "router", seed.classification);
  push("plan.completed", "router", seed.plan);

  for (const report of seed.specialists) push("specialist.started", report.specialist, { specialist: report.specialist });
  for (const item of seed.toolFlow) {
    push("tool.requested", item.agent, item);
    push("tool.completed", item.agent, item);
  }
  seed.evidence.forEach((item) => push("evidence.added", "investigator", item));
  seed.specialists.forEach((report) => push("specialist.completed", report.specialist, report));
  push("specialist.reconciled", "workflow", { specialists: seed.specialists.map((report) => report.specialist), conflicts: [] });
  seed.agentNotes.slice(1).forEach((note) => push("model.text_delta", note.agent, note));
  push("budget.updated", "workflow", {
    input_tokens: seed.usage.input_tokens,
    output_tokens: seed.usage.output_tokens,
    cache_read_tokens: 0,
    cache_creation_tokens: seed.usage.cache_creation_tokens,
    tool_calls: seed.usage.tool_calls,
  });
  push("diagnosis.completed", "investigator", seed.diagnosis);
  if (seed.action) push("action.proposed", "workflow", seed.action);
  push("investigation.completed", "workflow", { status: "completed" });

  return events.map((eventItem, index) => ({
    ...eventItem,
    sequence: index + 1,
    timestamp: new Date(Date.parse("2026-06-14T12:44:00.000Z") + (index + 1) * 8500).toISOString(),
  }));
}

function evidence(citationId: string, documentId: string, title: string, sourcePath: string, excerpt: string): Evidence {
  return {
    citation_id: citationId,
    document_id: documentId,
    chunk_id: `${documentId}#000`,
    title,
    source_path: sourcePath,
    excerpt,
    score: 0.032,
  };
}

function specialist(
  specialistName: SpecialistReport["specialist"],
  rationale: string,
  findings: string[],
  evidenceIds: string[],
): SpecialistReport {
  return {
    specialist: specialistName,
    status: "completed",
    rationale,
    findings,
    evidence_ids: evidenceIds,
    proposed_actions: [],
  };
}

function diagnosis(summary: string, rootCause: string, findings: string[], evidenceIds: string[], response: string): Diagnosis {
  return {
    summary,
    root_cause: rootCause,
    confidence: "high",
    findings: findings.map((claim, index) => ({ claim, evidence_ids: [evidenceIds[Math.min(index, evidenceIds.length - 1)]] })),
    citations: evidenceIds.map((evidence_id) => ({ evidence_id, supports: "Supports the diagnosis and recommended customer guidance." })),
    proposed_actions: ["Add an internal note summarizing the investigation and recommended response."],
    drafted_response: response,
  };
}

function action(id: string, caseId: string, title: string, rationale: string, evidenceIds: string[]): ProposedAction {
  return {
    id,
    action_type: "add_internal_note",
    service: "support",
    tool_name: "add_internal_note",
    title,
    rationale,
    arguments: { case_id: caseId, note: `TraceDesk replay recommendation: ${rationale}` },
    evidence_ids: evidenceIds,
    status: "pending",
    result: null,
    error: null,
    created_at: completedAt,
    decided_at: null,
    executed_at: null,
  };
}

function tool(agent: string, service: string, toolName: string, detail: string) {
  return { agent, service, tool: toolName, detail };
}
