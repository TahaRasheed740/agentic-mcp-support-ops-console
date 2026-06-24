import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { PublicDemoNotice } from "@/components/public-demo-notice";
import { formatDate, getInvestigations, titleCase } from "@/lib/api";
import { isPublicDemo } from "@/lib/config";

export default async function InvestigationsPage() {
  if (isPublicDemo) {
    return (
      <AppShell active="investigation">
        <PublicDemoNotice
          eyebrow="Live investigation history"
          title="Investigations"
          description="Live Claude investigation history belongs to the full local stack. In the public demo, the same investigation experience is available through captured replay scenarios."
        />
      </AppShell>
    );
  }

  const investigations = await getInvestigations();

  return (
    <AppShell active="investigation">
      <main className="content">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Live investigation history</p>
            <h1>Investigations</h1>
            <p>Review recent Claude-backed investigations, their evidence volume, action queue, and status.</p>
          </div>
          <span className="queue-total">{investigations.length} recent runs</span>
        </section>

        <section className="queue-panel investigation-index">
          <div className="case-row case-header" aria-hidden="true">
            <span>Investigation</span><span>Result</span><span>Evidence</span><span>Created</span>
          </div>
          {investigations.map((item) => (
            <Link className="case-row" href={`/investigations/${item.id}`} key={item.id}>
              <span className="case-primary">
                <span className={`priority-marker ${item.status === "failed" ? "urgent" : "normal"}`} />
                <span>
                  <strong>{item.case_id}</strong>
                  <small>{item.category ? titleCase(item.category) : "Classification pending"}</small>
                </span>
              </span>
              <span>
                <span className={`status-badge ${item.status}`}>{titleCase(item.status)}</span>
                {item.confidence && <small className="index-subtext">{titleCase(item.confidence)} confidence</small>}
              </span>
              <span className="date-cell">
                {item.evidence_count} evidence / {item.proposed_action_count} actions / {item.tool_calls} tools
              </span>
              <span className="date-cell">{formatDate(item.created_at)} UTC</span>
            </Link>
          ))}
          {!investigations.length && (
            <div className="empty-state">
              <strong>No live investigations yet</strong>
              <p>Open a support case and choose Investigate with Claude to create the first run.</p>
            </div>
          )}
        </section>
      </main>
    </AppShell>
  );
}
