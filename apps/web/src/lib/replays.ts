import type { Investigation, InvestigationEvent } from "@/lib/api";

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

const completedAt = "2026-06-14T12:48:00.000Z";

export const replayScenarios: ReplayScenario[] = [
  {
    id: "eu-webhook-latency",
    title: "EU Webhook Latency",
    summary:
      "A support engineer investigates delayed EU webhook deliveries, separates queue delay from endpoint failure, and prepares a safe customer response.",
    caseId: "TKT-1007",
    duration: "4 min replay",
    tags: ["Reliability", "Specialists", "Approval queue"],
    investigation: {
      id: "replay-eu-webhook-latency",
      case_id: "TKT-1007",
      status: "completed",
      router_model: "claude-haiku-4-5",
      investigator_model: "claude-sonnet-4-5",
      classification: {
        category: "reliability",
        urgency: "urgent",
        complexity: "complex",
        summary:
          "EU webhook delivery latency increased while US deliveries and endpoint acknowledgements stayed healthy.",
        rationale:
          "The symptom is production-impacting, region-specific, and requires correlating documentation, account context, and incident evidence.",
      },
      plan: {
        hypotheses: [
          "A regional queue backlog delayed dispatch before webhook execution.",
          "Customer endpoint latency is a distractor because acknowledgements stayed normal.",
          "Manual retries would add work to the same affected queue.",
        ],
        evidence_needed: [
          "Current regional latency guidance",
          "Incident review matching region and timeline",
          "Recent run timing showing recovery",
          "Integration and account context",
        ],
        allowed_tools: [
          "search_knowledge",
          "get_integration",
          "list_recent_runs",
          "list_incidents",
        ],
        steps: [
          "Classify the issue and choose relevant specialists.",
          "Search current documentation and incident evidence.",
          "Inspect integration and recent run context.",
          "Reconcile findings and draft a customer-safe response.",
        ],
      },
      diagnosis: {
        summary:
          "Summit Labs experienced elevated EU webhook delivery latency that matches incident INC-001. Evidence indicates queue time increased before dispatch while execution duration and customer endpoint responses remained healthy.",
        root_cause:
          "A worker queue imbalance in eu-west delayed dispatch. The incident record says the platform-side issue is documented as mitigated by the Acme Automations platform team.",
        confidence: "high",
        findings: [
          {
            claim:
              "The incident review describes a eu-west worker queue imbalance that delayed webhook dispatch without data loss.",
            evidence_ids: ["E1"],
          },
          {
            claim:
              "Current guidance says region-specific latency should be correlated with incidents before changing customer configuration.",
            evidence_ids: ["E2"],
          },
          {
            claim:
              "Recent run context shows the latest run returned to normal latency after the incident window.",
            evidence_ids: ["E3"],
          },
        ],
        citations: [
          {
            evidence_id: "E1",
            supports:
              "Supports the platform-side incident, affected region, queue-delay failure mode, and no-data-loss conclusion.",
          },
          {
            evidence_id: "E2",
            supports:
              "Supports avoiding endpoint or secret changes when the regional incident and run timing match.",
          },
          {
            evidence_id: "E3",
            supports:
              "Supports the recovery statement by showing the most recent run returned to baseline latency.",
          },
        ],
        proposed_actions: [
          "Add an internal note summarizing the incident correlation and customer guidance.",
        ],
        drafted_response:
          "We found that your EU webhook deliveries were delayed by a regional Acme Automations queue issue, not by your endpoint. The incident evidence indicates the platform-side issue was mitigated by the Acme Automations platform team. Deliveries were delayed rather than lost, and no customer-side action such as rotating secrets, changing endpoints, or manually retrying jobs is recommended.",
      },
      drafted_response:
        "We found that your EU webhook deliveries were delayed by a regional Acme Automations queue issue, not by your endpoint. The incident evidence indicates the platform-side issue was mitigated by the Acme Automations platform team. Deliveries were delayed rather than lost, and no customer-side action such as rotating secrets, changing endpoints, or manually retrying jobs is recommended.",
      specialist_reports: [
        {
          specialist: "documentation",
          status: "completed",
          rationale:
            "Searched current support documentation and incident PDFs for the exact regional latency symptom.",
          findings: [
            "Current guidance warns against customer endpoint changes when queue delay is region-specific.",
            "The incident review matches eu-west, webhook delivery, and queue-delay symptoms.",
          ],
          evidence_ids: ["E1", "E2"],
          proposed_actions: [],
        },
        {
          specialist: "account",
          status: "completed",
          rationale:
            "Checked account and integration context before proposing any support-state mutation.",
          findings: [
            "Summit Labs is on the Scale plan in eu-west.",
            "The production webhook integration remains connected.",
          ],
          evidence_ids: [],
          proposed_actions: ["Add a concise internal note for support continuity."],
        },
        {
          specialist: "reliability",
          status: "completed",
          rationale:
            "Correlated incident timing with recent run behavior without retrying or changing jobs.",
          findings: [
            "INC-001 describes a 47-minute eu-west queue imbalance.",
            "Recent runs show recovery to baseline after the incident window.",
          ],
          evidence_ids: ["E1", "E3"],
          proposed_actions: [],
        },
      ],
      proposed_actions: [
        {
          id: "replay-action-note",
          action_type: "add_internal_note",
          service: "support",
          tool_name: "add_internal_note",
          title: "Add consolidated investigation note",
          rationale:
            "Record the incident correlation, no-customer-action guidance, and supporting evidence in the ticket.",
          arguments: {
            case_id: "TKT-1007",
            note: "TraceDesk replay recommendation: document INC-001 correlation and advise no customer-side changes.",
          },
          evidence_ids: ["E1", "E2", "E3"],
          status: "pending",
          result: null,
          error: null,
          created_at: completedAt,
          decided_at: null,
          executed_at: null,
        },
      ],
      evidence: [
        {
          citation_id: "E1",
          document_id: "eu-latency-incident-review",
          chunk_id: "eu-latency-incident-review#000",
          title: "Incident review - EU delivery latency",
          source_path: "output/pdf/acme-incident-review-eu-latency.pdf",
          excerpt:
            "A worker queue imbalance in eu-west increased webhook queue time for 47 minutes. Payload execution time and customer endpoint response time remained normal. No customer configuration change was required.",
          score: 0.03279,
        },
        {
          citation_id: "E2",
          document_id: "regional-delivery-latency",
          chunk_id: "regional-delivery-latency#000",
          title: "Investigating region-specific delivery latency",
          source_path: "knowledge/docs/regional-delivery-latency.md",
          excerpt:
            "Latency isolated to one region with healthy destinations should be correlated with the regional incident timeline before changing customer configuration.",
          score: 0.03226,
        },
        {
          citation_id: "E3",
          document_id: "recent-run-summary",
          chunk_id: "recent-run-summary#000",
          title: "Recent run timing summary",
          source_path: "simulated operations MCP",
          excerpt:
            "run_00067 completed in 1.8 seconds after the incident window, while earlier affected runs showed elevated queue timing. Endpoint responses were normal once dispatch occurred.",
          score: null,
        },
      ],
      input_tokens: 2330,
      output_tokens: 546,
      cache_read_tokens: 0,
      cache_creation_tokens: 2027,
      tool_calls: 11,
      error: null,
      created_at: "2026-06-14T12:44:00.000Z",
      started_at: "2026-06-14T12:44:03.000Z",
      completed_at: completedAt,
    },
    events: [
      event(1, "investigation.created", "workflow", { case_id: "TKT-1007", status: "queued" }),
      event(2, "investigation.started", "workflow", { status: "running" }),
      event(3, "classification.completed", "router", {
        category: "reliability",
        urgency: "urgent",
        complexity: "complex",
        summary:
          "EU webhook delivery latency increased while US deliveries and endpoint acknowledgements stayed healthy.",
        rationale:
          "The issue is region-specific and production-impacting, so specialists should inspect documentation, account context, and reliability evidence.",
      }),
      event(4, "specialist.started", "documentation", { specialist: "documentation" }),
      event(5, "specialist.started", "account", { specialist: "account" }),
      event(6, "specialist.started", "reliability", { specialist: "reliability" }),
      event(7, "evidence.added", "documentation", { citation_id: "E1", title: "Incident review - EU delivery latency" }),
      event(8, "evidence.added", "documentation", { citation_id: "E2", title: "Investigating region-specific delivery latency" }),
      event(9, "specialist.completed", "documentation", { specialist: "documentation", status: "completed" }),
      event(10, "specialist.completed", "account", { specialist: "account", status: "completed" }),
      event(11, "specialist.completed", "reliability", { specialist: "reliability", status: "completed" }),
      event(12, "specialist.reconciled", "workflow", { specialists: ["documentation", "account", "reliability"], conflicts: [] }),
      event(13, "evidence.added", "investigator", { citation_id: "E3", title: "Recent run timing summary" }),
      event(14, "diagnosis.completed", "investigator", {
        summary:
          "The evidence supports a platform-side eu-west queue delay rather than a customer endpoint issue.",
        confidence: "high",
      }),
      event(15, "action.proposed", "workflow", { id: "replay-action-note", status: "pending", title: "Add consolidated investigation note" }),
      event(16, "investigation.completed", "workflow", { status: "completed" }),
    ],
  },
];

export function getReplayScenario(id: string): ReplayScenario | undefined {
  return replayScenarios.find((scenario) => scenario.id === id);
}

function event(
  sequence: number,
  eventType: string,
  agent: string,
  payload: Record<string, unknown>,
): InvestigationEvent {
  return {
    sequence,
    timestamp: new Date(Date.parse("2026-06-14T12:44:00.000Z") + sequence * 9500).toISOString(),
    event_type: eventType,
    agent,
    payload,
  };
}
