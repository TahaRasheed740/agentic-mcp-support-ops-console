import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { EvidenceExcerpt } from "@/components/evidence-excerpt";
import { PublicDemoNotice } from "@/components/public-demo-notice";
import { searchKnowledge, titleCase } from "@/lib/api";
import { isPublicDemo } from "@/lib/config";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function KnowledgePage({ searchParams }: { searchParams: SearchParams }) {
  if (isPublicDemo) {
    return (
      <AppShell active="knowledge">
        <PublicDemoNotice
          eyebrow="Evidence library"
          title="Knowledge search"
          description="Hybrid BM25 plus vector retrieval is part of the full local stack. The public deployment keeps this page read-only so the hosted demo does not need the backend or pgvector database."
        />
      </AppShell>
    );
  }

  const params = await searchParams;
  const query = singleValue(params.q) ?? "";
  const requestedMode = singleValue(params.mode);
  const mode = isMode(requestedMode) ? requestedMode : "hybrid";
  const results = await searchKnowledge(query, mode);

  return (
    <AppShell active="knowledge">
      <main className="content knowledge-page">
        <section className="page-heading knowledge-heading">
          <div>
            <p className="eyebrow">Evidence library</p>
            <h1>Knowledge search</h1>
            <p>Inspect what TraceDesk retrieves before this evidence is placed in an agent context.</p>
          </div>
          <span className="queue-total">40 versioned sources</span>
        </section>

        <form className="knowledge-search">
          <input
            aria-label="Knowledge query"
            name="q"
            defaultValue={query}
            placeholder="Describe a customer symptom or paste a ticket question"
            required
          />
          <select aria-label="Retrieval mode" name="mode" defaultValue={mode}>
            <option value="hybrid">Hybrid: semantic + BM25</option>
            <option value="semantic">Semantic only</option>
            <option value="lexical">BM25 only</option>
          </select>
          <button type="submit">Search evidence</button>
        </form>

        {!query && (
          <section className="knowledge-empty">
            <span>Try a benchmark symptom</span>
            <div>
              <Link href="/knowledge?q=webhook+401+after+secret+rotation">Webhook 401 after secret rotation</Link>
              <Link href="/knowledge?q=EU+delivery+queue+latency">EU delivery queue latency</Link>
              <Link href="/knowledge?q=CSV+timestamps+wrong+timezone">CSV timestamps and time zones</Link>
            </div>
          </section>
        )}

        {query && (
          <section className="evidence-layout">
            <div className="evidence-summary">
              <span>{results.items.length} sources</span>
              <strong>{titleCase(results.mode)} retrieval</strong>
              <p>Results expose each contributing rank. Reciprocal-rank fusion rewards agreement between methods.</p>
            </div>
            <div className="evidence-list">
              {results.items.map((item, index) => (
                <article className={`evidence-card ${item.status}`} key={item.chunk_id}>
                  <div className="evidence-rank">{String(index + 1).padStart(2, "0")}</div>
                  <div>
                    <div className="evidence-meta">
                      <span>{titleCase(item.product_area)}</span>
                      <span>v{item.version}</span>
                      <span>{item.source_type.toUpperCase()}</span>
                      <span className={`source-status ${item.status}`}>{titleCase(item.status)}</span>
                    </div>
                    <h2>{item.title}</h2>
                    <p className="chunk-heading">{item.heading}</p>
                    <EvidenceExcerpt content={item.content} contentId={`evidence-${item.chunk_id}`} />
                    <div className="rank-details">
                      <span>Semantic rank <strong>{item.semantic_rank ?? "-"}</strong></span>
                      <span>BM25 rank <strong>{item.lexical_rank ?? "-"}</strong></span>
                      <span>RRF score <strong>{item.score.toFixed(5)}</strong></span>
                      <code>{item.document_id}</code>
                    </div>
                  </div>
                </article>
              ))}
              {results.items.length === 0 && <div className="empty-state">No evidence matched this query.</div>}
            </div>
          </section>
        )}
      </main>
    </AppShell>
  );
}

function singleValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function isMode(value: string | undefined): value is "hybrid" | "semantic" | "lexical" {
  return value === "hybrid" || value === "semantic" || value === "lexical";
}
