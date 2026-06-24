import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { InvestigationWorkspace } from "@/components/investigation-workspace";
import { PublicDemoNotice } from "@/components/public-demo-notice";
import { getInvestigation } from "@/lib/api";
import { isPublicDemo } from "@/lib/config";

export default async function InvestigationPage({ params }: { params: Promise<{ investigationId: string }> }) {
  const { investigationId } = await params;
  if (isPublicDemo) {
    return (
      <AppShell active="investigation">
        <PublicDemoNotice
          eyebrow="Live investigation"
          title={investigationId}
          description="Live investigation records are loaded from the local backend. The public deployment exposes captured replays instead, so visitors can inspect the same workflow without live model access."
        />
      </AppShell>
    );
  }

  const investigation = await getInvestigation(investigationId);
  if (!investigation) notFound();
  return <AppShell active="investigation"><main className="content investigation-page"><InvestigationWorkspace initial={investigation} /></main></AppShell>;
}
