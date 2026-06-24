import { AppShell } from "@/components/app-shell";
import { formatDate, getEvaluationReport, titleCase } from "@/lib/api";

export default async function EvaluationsPage() {
  const report = await getEvaluationReport();
  const metrics = Object.entries(report.metrics);

  return (
    <AppShell active="evaluations">
      <main className="content evaluation-page">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Regression quality</p>
            <h1>Evaluations</h1>
            <p>
              Deterministic CI-safe grading over the benchmark set, adversarial prompts, citations,
              and approval-gated write safety.
            </p>
          </div>
          <span className={`queue-total ${report.passed ? "pass" : "fail"}`}>
            {report.passed ? "Passing" : "Failing"} / v{report.dataset_version}
          </span>
        </section>

        <section className="metric-grid evaluation-metrics">
          {metrics.map(([metric, value]) => (
            <article className="metric-card green" key={metric}>
              <span>{titleCase(metric)}</span>
              <strong>{Math.round(value * 100)}%</strong>
            </article>
          ))}
        </section>

        <div className="detail-grid">
          <section className="panel">
            <div className="panel-heading">
              <div><span>Threshold status</span><h2>Failures</h2></div>
              <span>{formatDate(report.generated_at)} UTC</span>
            </div>
            {report.failures.length ? report.failures.map((failure) => (
              <div className="eval-row failed" key={failure.metric}>
                <strong>{titleCase(failure.metric)}</strong>
                <span>{Math.round(failure.actual * 100)}% below {Math.round(failure.threshold * 100)}%</span>
              </div>
            )) : <p className="muted-copy">No threshold failures. Empty failure sections are shown intentionally rather than hidden.</p>}
          </section>

          <aside className="case-sidebar">
            <section className="panel fact-panel">
              <span className="panel-label">Failed cases</span>
              <h2>{report.failed_cases.length}</h2>
              <p className="eval-note">Failures would be listed here by ticket ID for review.</p>
            </section>
            <section className="panel fact-panel">
              <span className="panel-label">Adversarial checks</span>
              <h2>{report.adversarial_cases.length}</h2>
              {report.adversarial_cases.map((item) => (
                <Fact key={item.id} label={item.id} value={item.prompt_injection_blocked ? "Blocked" : "Failed"} />
              ))}
            </section>
          </aside>
        </div>

        <section className="panel evaluation-note">
          <div className="panel-heading"><div><span>Scope note</span><h2>What This Measures</h2></div></div>
          <p>{report.cost_latency_note}</p>
        </section>

        <section className="panel evaluation-note">
          <div className="panel-heading"><div><span>Optional judge</span><h2>Model-Based Grading</h2></div></div>
          {report.model_grading.enabled ? (
            <p>
              Claude judged {report.model_grading.cases_graded} of {report.model_grading.total_cases} benchmark cases
              with {report.model_grading.model}. Pass rate:{" "}
              {Math.round((report.model_grading.pass_rate ?? 0) * 100)}%. Tokens:{" "}
              {report.model_grading.input_tokens ?? 0} input, {report.model_grading.output_tokens ?? 0} output.
            </p>
          ) : (
            <p>
              {report.model_grading.reason} This is kept manual so CI and public demos do not spend Anthropic tokens.
            </p>
          )}
        </section>
      </main>
    </AppShell>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div className="fact-row"><span>{label}</span><strong>{value}</strong></div>;
}
