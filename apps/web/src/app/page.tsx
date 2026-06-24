import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { isPublicDemo } from "@/lib/config";
import { formatDate, getCases, titleCase } from "@/lib/api";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function SupportQueue({ searchParams }: { searchParams: SearchParams }) {
  if (isPublicDemo) return <PublicDemoHome />;

  const params = await searchParams;
  const status = singleValue(params.status);
  const priority = singleValue(params.priority);
  const search = singleValue(params.search);
  const requestedPage = Number(singleValue(params.page) ?? "1");
  const page = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  const cases = await getCases({ status, priority, search, page });
  const pageCount = Math.max(1, Math.ceil(cases.total / cases.page_size));

  return (
    <AppShell>
      <main className="content">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Customer operations</p>
            <h1>Support queue</h1>
            <p>Review active customer issues before evidence-grounded investigations are added.</p>
          </div>
          <span className="queue-total">{cases.total} matching cases</span>
        </section>

        <section className="metric-grid" aria-label="Queue summary">
          <Metric label="Open" value={cases.status_counts.open ?? 0} tone="orange" />
          <Metric label="Investigating" value={cases.status_counts.investigating ?? 0} tone="blue" />
          <Metric label="Waiting on customer" value={cases.status_counts.pending ?? 0} tone="purple" />
          <Metric label="Resolved" value={cases.status_counts.resolved ?? 0} tone="green" />
        </section>

        <section className="queue-panel">
          <div className="queue-toolbar">
            <div className="filter-tabs" aria-label="Case status filters">
              <FilterLink label="All" active={!status} params={{ priority, search }} />
              {Object.entries(cases.status_counts).map(([filterStatus, count]) => (
                <FilterLink
                  key={filterStatus}
                  label={`${titleCase(filterStatus)} ${count}`}
                  active={status === filterStatus}
                  params={{ status: filterStatus, priority, search }}
                />
              ))}
            </div>
            <form className="search-form">
              {status && <input type="hidden" name="status" value={status} />}
              {priority && <input type="hidden" name="priority" value={priority} />}
              <input name="search" defaultValue={search} placeholder="Search cases or organizations" />
              <button type="submit">Search</button>
            </form>
          </div>

          <div className="case-list">
            <div className="case-row case-header" aria-hidden="true">
              <span>Case</span><span>Customer</span><span>Status</span><span>Updated</span>
            </div>
            {cases.items.map((supportCase) => (
              <Link className="case-row" href={`/cases/${supportCase.id}`} key={supportCase.id}>
                <span className="case-primary">
                  <span className={`priority-marker ${supportCase.priority}`} />
                  <span>
                    <strong>{supportCase.subject}</strong>
                    <small>{supportCase.id} / {titleCase(supportCase.category)}</small>
                  </span>
                </span>
                <span className="customer-cell">
                  <strong>{supportCase.organization.name}</strong>
                  <small>{supportCase.organization.plan} / {supportCase.organization.region}</small>
                </span>
                <span><span className={`status-badge ${supportCase.status}`}>{titleCase(supportCase.status)}</span></span>
                <span className="date-cell">{formatDate(supportCase.updated_at)} UTC</span>
              </Link>
            ))}
            {cases.items.length === 0 && (
              <div className="empty-state"><strong>No cases found</strong><p>Try removing a filter or using a broader search.</p></div>
            )}
          </div>
          {pageCount > 1 && (
            <div className="pagination" aria-label="Case list pagination">
              <PageLink
                label="Previous"
                disabled={cases.page <= 1}
                params={{ status, priority, search, page: String(cases.page - 1) }}
              />
              <span>Page {cases.page} of {pageCount}</span>
              <PageLink
                label="Next"
                disabled={cases.page >= pageCount}
                params={{ status, priority, search, page: String(cases.page + 1) }}
              />
            </div>
          )}
        </section>
      </main>
    </AppShell>
  );
}

function PublicDemoHome() {
  return (
    <AppShell active="replays">
      <main className="content">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Public replay demo</p>
            <h1>TraceDesk</h1>
            <p>
              Explore real captured Claude investigation runs from an agentic support operations console. This hosted
              demo is replay-safe: it does not call Claude, require credentials, or change support data.
            </p>
          </div>
          <Link className="evidence-button" href="/replays">Open recorded replays</Link>
        </section>

        <section className="metric-grid">
          <Metric label="Captured replays" value={4} tone="green" />
          <Metric label="MCP services" value={3} tone="blue" />
          <Metric label="Benchmark cases" value={15} tone="purple" />
          <Metric label="Public API spend" value={0} tone="orange" />
        </section>

        <section className="panel demo-notice">
          <span className="panel-label">What this shows</span>
          <h2>Replay-safe view of the full system</h2>
          <p>
            The public link focuses on step-by-step investigation playback: routing, tool calls, evidence, specialist
            reports, citations, drafted responses, and approval queues. The repository contains the complete local
            stack for live Claude investigations, RAG over synthetic documentation, MCP tools, evaluations, and Docker.
          </p>
          <div className="demo-actions">
            <Link className="evidence-button" href="/replays">Start with replays</Link>
            <a
              className="page-link"
              href="https://github.com/TahaRasheed740/agentic-mcp-support-ops-console"
            >
              View full repository
            </a>
          </div>
        </section>
      </main>
    </AppShell>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return <article className={`metric-card ${tone}`}><span>{label}</span><strong>{value}</strong></article>;
}

function FilterLink({
  label,
  active,
  params,
}: {
  label: string;
  active: boolean;
  params: Record<string, string | undefined>;
}) {
  const target = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value) target.set(key, value);
  return <Link className={active ? "active" : ""} href={`/?${target}`}>{label}</Link>;
}

function singleValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function PageLink({
  label,
  disabled,
  params,
}: {
  label: string;
  disabled: boolean;
  params: Record<string, string | undefined>;
}) {
  if (disabled) return <span className="page-link disabled">{label}</span>;
  const target = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value) target.set(key, value);
  return <Link className="page-link" href={`/?${target}`}>{label}</Link>;
}
