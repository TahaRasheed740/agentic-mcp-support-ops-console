export type Persona = {
  id: string;
  name: string;
  role: string;
  initials: string;
  specialty: string;
};

export type DemoSession = {
  id: string;
  persona: Persona;
  created_at: string;
  reset_at: string | null;
};

export type Organization = {
  id: string;
  name: string;
  plan: string;
  region: string;
  status: string;
};

export type Integration = {
  id: string;
  name: string;
  kind: string;
  status: string;
  environment: string;
  last_seen_at: string;
};

export type SupportCase = {
  id: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  created_at: string;
  updated_at: string;
  organization: Organization;
  integration: Integration | null;
};

export type CaseListResponse = {
  items: SupportCase[];
  total: number;
  page: number;
  page_size: number;
  status_counts: Record<string, number>;
};

export type CaseDetail = SupportCase & {
  requester: { id: string; name: string; email: string; role: string };
  recent_runs: Array<{
    id: string;
    status: string;
    started_at: string;
    duration_ms: number;
    error_code: string | null;
    records_processed: number;
  }>;
  related_incidents: Array<{
    id: string;
    title: string;
    status: string;
    severity: string;
    region: string;
    started_at: string;
  }>;
  organization_members: number;
  organization_open_cases: number;
};

export type EvidenceItem = {
  chunk_id: string;
  document_id: string;
  title: string;
  heading: string;
  product_area: string;
  version: string;
  status: string;
  source_type: string;
  source_path: string;
  content: string;
  score: number;
  semantic_rank: number | null;
  lexical_rank: number | null;
};

export type KnowledgeSearchResponse = {
  query: string;
  mode: "hybrid" | "semantic" | "lexical";
  items: EvidenceItem[];
};

export type MCPTool = {
  name: string;
  description: string | null;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown> | null;
};

export type MCPServer = {
  name: "knowledge" | "operations" | "support";
  tools: MCPTool[];
  resources: Array<{ uri: string; name: string; description: string | null; mime_type: string | null }>;
  prompts: Array<{ name: string; description: string | null }>;
};

export type MCPCatalog = { servers: MCPServer[] };

export type Classification = {
  category: string;
  urgency: "low" | "normal" | "high" | "urgent";
  complexity: "simple" | "moderate" | "complex";
  summary: string;
  rationale: string;
};

export type InvestigationPlan = {
  hypotheses: string[];
  evidence_needed: string[];
  allowed_tools: string[];
  steps: string[];
};

export type Diagnosis = {
  summary: string;
  root_cause: string;
  confidence: "low" | "medium" | "high";
  findings: Array<{ claim: string; evidence_ids: string[] }>;
  citations: Array<{ evidence_id: string; supports: string }>;
  proposed_actions: string[];
  drafted_response: string;
};

export type SpecialistReport = {
  specialist: "documentation" | "account" | "reliability";
  status: "completed" | "skipped" | "conflict";
  rationale: string;
  findings: string[];
  evidence_ids: string[];
  proposed_actions: string[];
};

export type ProposedAction = {
  id: string;
  action_type: "add_internal_note" | "update_ticket_status";
  service: "support";
  tool_name: "add_internal_note" | "update_ticket_status";
  title: string;
  rationale: string;
  arguments: Record<string, unknown>;
  evidence_ids: string[];
  status: "pending" | "approved" | "rejected" | "executing" | "executed" | "stale" | "failed";
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  decided_at: string | null;
  executed_at: string | null;
};

export type InvestigationEvidence = {
  citation_id: string;
  document_id: string;
  chunk_id: string;
  title: string;
  source_path: string;
  excerpt: string;
  score: number | null;
};

export type Investigation = {
  id: string;
  case_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  router_model: string;
  investigator_model: string;
  classification: Classification | null;
  plan: InvestigationPlan | null;
  diagnosis: Diagnosis | null;
  drafted_response: string | null;
  specialist_reports: SpecialistReport[];
  proposed_actions: ProposedAction[];
  evidence: InvestigationEvidence[];
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_creation_tokens: number;
  tool_calls: number;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type InvestigationEvent = {
  sequence: number;
  timestamp: string;
  event_type: string;
  agent: string;
  payload: Record<string, unknown>;
};

export type InvestigationListItem = {
  id: string;
  case_id: string;
  status: Investigation["status"];
  category: string | null;
  confidence: "low" | "medium" | "high" | null;
  summary: string | null;
  tool_calls: number;
  evidence_count: number;
  proposed_action_count: number;
  created_at: string;
  completed_at: string | null;
};

export type EvaluationReport = {
  dataset_version: string;
  generated_at: string;
  thresholds: Record<string, number>;
  metrics: Record<string, number>;
  passed: boolean;
  failures: Array<{ metric: string; actual: number; threshold: number }>;
  failed_cases: Array<{ ticket_id: string }>;
  adversarial_cases: Array<{ id: string; prompt_injection_blocked: boolean }>;
  cost_latency_note: string;
};

const internalApiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8001";

export async function getCases(filters: {
  status?: string;
  priority?: string;
  search?: string;
  page?: number;
}): Promise<CaseListResponse> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.search) params.set("search", filters.search);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", "25");

  const response = await fetch(`${internalApiUrl}/api/v1/cases?${params}`, {
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Unable to load support cases");
  return (await response.json()) as CaseListResponse;
}

export async function getCase(caseId: string): Promise<CaseDetail | null> {
  const response = await fetch(`${internalApiUrl}/api/v1/cases/${caseId}`, {
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Unable to load support case");
  return (await response.json()) as CaseDetail;
}

export async function searchKnowledge(
  query: string,
  mode: "hybrid" | "semantic" | "lexical" = "hybrid",
): Promise<KnowledgeSearchResponse> {
  if (!query.trim()) return { query, mode, items: [] };
  const params = new URLSearchParams({ q: query, mode, limit: "8" });
  const response = await fetch(`${internalApiUrl}/api/v1/knowledge/search?${params}`, {
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Unable to search the knowledge base");
  return (await response.json()) as KnowledgeSearchResponse;
}

export async function getMCPCatalog(): Promise<MCPCatalog> {
  const response = await fetch(`${internalApiUrl}/api/v1/mcp/servers`, { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to inspect MCP services");
  return (await response.json()) as MCPCatalog;
}

export async function getInvestigation(id: string): Promise<Investigation | null> {
  const response = await fetch(`${internalApiUrl}/api/v1/investigations/${id}`, { cache: "no-store" });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Unable to load investigation");
  return (await response.json()) as Investigation;
}

export async function getInvestigations(): Promise<InvestigationListItem[]> {
  const response = await fetch(`${internalApiUrl}/api/v1/investigations`, { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to load investigations");
  return (await response.json()) as InvestigationListItem[];
}

export async function getEvaluationReport(): Promise<EvaluationReport> {
  const response = await fetch(`${internalApiUrl}/api/v1/evaluations/latest`, { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to load evaluation report");
  return (await response.json()) as EvaluationReport;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(new Date(value));
}

export function titleCase(value: string): string {
  return value
    .replaceAll("_", " ")
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
