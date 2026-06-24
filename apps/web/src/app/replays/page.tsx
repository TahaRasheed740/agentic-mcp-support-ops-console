import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { replayScenarios } from "@/lib/replays";

export default function ReplaysPage() {
  return (
    <AppShell active="replays">
      <main className="content replay-page">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Anonymous demo mode</p>
            <h1>Recorded replays</h1>
            <p>
              Watch canonical investigations without an Anthropic API key. Replays use frozen synthetic data and
              clearly separate demonstration playback from live execution.
            </p>
          </div>
          <span className="queue-total">{replayScenarios.length} replay scenarios</span>
        </section>

        <section className="replay-list">
          {replayScenarios.length ? replayScenarios.map((scenario) => (
            <Link className="replay-card panel" href={`/replays/${scenario.id}`} key={scenario.id}>
              <div>
                <span className="panel-label">{scenario.caseId} / {scenario.duration}</span>
                <h2>{scenario.title}</h2>
                <p>{scenario.summary}</p>
              </div>
              <div className="replay-tags">
                {scenario.tags.map((tag) => <span key={tag}>{tag}</span>)}
              </div>
            </Link>
          )) : (
            <div className="panel empty-state">
              <span>No captured replays yet</span>
              <p>
                Replays will appear here after live Claude investigations are run locally and exported.
                No scripted or simulated replay is being presented as a recording.
              </p>
            </div>
          )}
        </section>
      </main>
    </AppShell>
  );
}
