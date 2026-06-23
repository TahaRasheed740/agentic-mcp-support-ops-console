import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { InvestigationWorkspace } from "@/components/investigation-workspace";
import { getReplayScenario } from "@/lib/replays";

export default async function ReplayPage({ params }: { params: Promise<{ replayId: string }> }) {
  const { replayId } = await params;
  const replay = getReplayScenario(replayId);
  if (!replay) notFound();

  return (
    <AppShell active="replays">
      <main className="content investigation-page">
        <div className="breadcrumbs">
          <Link href="/replays">Recorded replays</Link><span>/</span>{replay.title}
        </div>
        <InvestigationWorkspace
          initial={replay.investigation}
          initialEvents={replay.events}
          mode="replay"
          replaySummary={replay.summary}
        />
      </main>
    </AppShell>
  );
}
