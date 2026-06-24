import Link from "next/link";

export function PublicDemoNotice({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <main className="content">
      <section className="page-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <Link className="page-link" href="/replays">Open replays</Link>
      </section>

      <section className="panel demo-notice">
        <span className="panel-label">Public replay demo</span>
        <h2>Available in the full local stack</h2>
        <p>
          This hosted version focuses on captured investigation playback so visitors can explore the agent workflow
          without credentials, live Claude calls, or backend infrastructure. The complete GitHub project still includes
          the FastAPI backend, PostgreSQL/pgvector database, MCP services, RAG pipeline, live investigations, and
          evaluation tooling for local/private demos.
        </p>
        <div className="demo-actions">
          <Link className="evidence-button" href="/replays">View captured investigations</Link>
          <a
            className="page-link"
            href="https://github.com/TahaRasheed740/agentic-mcp-support-ops-console"
          >
            View full repository
          </a>
        </div>
      </section>
    </main>
  );
}

