import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { InvestigationLaunchButton } from "@/components/investigation-launch-button";
import { formatDate, getCase, getRuntimeCapabilities, titleCase } from "@/lib/api";

export default async function CasePage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const [supportCase, runtime] = await Promise.all([
    getCase(caseId),
    getRuntimeCapabilities(),
  ]);
  if (!supportCase) notFound();

  return (
    <AppShell>
      <main className="content case-detail-page">
        <div className="breadcrumbs"><Link href="/">Support queue</Link><span>/</span>{supportCase.id}</div>
        <section className="case-title-block">
          <div>
            <div className="case-kicker">
              <span className={`priority-label ${supportCase.priority}`}>{titleCase(supportCase.priority)} priority</span>
              <span className={`status-badge ${supportCase.status}`}>{titleCase(supportCase.status)}</span>
            </div>
            <h1>{supportCase.subject}</h1>
            <p>{supportCase.description}</p>
          </div>
          <div className="case-actions">
            <Link
              className="evidence-button"
              href={`/knowledge?q=${encodeURIComponent(`${supportCase.subject} ${supportCase.description}`)}`}
            >
              Find evidence
            </Link>
            <InvestigationLaunchButton caseId={supportCase.id} runtime={runtime} />
          </div>
        </section>

        <div className="detail-grid">
          <div className="detail-main">
            <section className="panel">
              <div className="panel-heading"><div><span>Operational context</span><h2>Recent job runs</h2></div><span>{supportCase.integration?.name ?? "No integration"}</span></div>
              <div className="run-list">
                {supportCase.recent_runs.map((run) => (
                  <div className="run-row" key={run.id}>
                    <span className={`run-state ${run.status}`} />
                    <span><strong>{run.id}</strong><small>{formatDate(run.started_at)} UTC</small></span>
                    <span>{run.records_processed.toLocaleString()} records</span>
                    <span>{run.duration_ms.toLocaleString()} ms</span>
                    <span className={run.error_code ? "error-code" : "success-code"}>{run.error_code ?? "Completed"}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading"><div><span>Reliability context</span><h2>Related incidents</h2></div></div>
              {supportCase.related_incidents.length ? supportCase.related_incidents.map((incident) => (
                <div className="incident-row" key={incident.id}>
                  <span className={`severity ${incident.severity}`}>{incident.severity.toUpperCase()}</span>
                  <span><strong>{incident.title}</strong><small>{incident.region} / Started {formatDate(incident.started_at)} UTC</small></span>
                  <span className={`status-badge ${incident.status}`}>{titleCase(incident.status)}</span>
                </div>
              )) : <p className="muted-copy">No incidents match this organization&apos;s region.</p>}
            </section>
          </div>

          <aside className="case-sidebar">
            <section className="panel fact-panel">
              <span className="panel-label">Customer</span>
              <h2>{supportCase.organization.name}</h2>
              <Fact label="Plan" value={supportCase.organization.plan} />
              <Fact label="Region" value={supportCase.organization.region} />
              <Fact label="Members" value={String(supportCase.organization_members)} />
              <Fact label="Open cases" value={String(supportCase.organization_open_cases)} />
            </section>
            <section className="panel fact-panel">
              <span className="panel-label">Requester</span>
              <h2>{supportCase.requester.name}</h2>
              <Fact label="Role" value={titleCase(supportCase.requester.role)} />
              <Fact label="Email" value={supportCase.requester.email} />
              <Fact label="Created" value={`${formatDate(supportCase.created_at)} UTC`} />
            </section>
            {supportCase.integration && (
              <section className="panel fact-panel">
                <span className="panel-label">Integration</span>
                <h2>{supportCase.integration.name}</h2>
                <Fact label="Type" value={titleCase(supportCase.integration.kind)} />
                <Fact label="Environment" value={titleCase(supportCase.integration.environment)} />
                <Fact label="Connection" value={titleCase(supportCase.integration.status)} />
              </section>
            )}
          </aside>
        </div>
      </main>
    </AppShell>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div className="fact-row"><span>{label}</span><strong>{value}</strong></div>;
}
