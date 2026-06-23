import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { InvestigationWorkspace } from "@/components/investigation-workspace";
import { getInvestigation } from "@/lib/api";

export default async function InvestigationPage({ params }: { params: Promise<{ investigationId: string }> }) {
  const { investigationId } = await params;
  const investigation = await getInvestigation(investigationId);
  if (!investigation) notFound();
  return <AppShell active="investigation"><main className="content investigation-page"><InvestigationWorkspace initial={investigation} /></main></AppShell>;
}
