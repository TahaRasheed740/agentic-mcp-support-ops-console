import { AppShell } from "@/components/app-shell";
import { PublicDemoNotice } from "@/components/public-demo-notice";
import { ToolExplorer } from "@/components/tool-explorer";
import { getMCPCatalog } from "@/lib/api";
import { isPublicDemo } from "@/lib/config";

export default async function ToolsPage() {
  if (isPublicDemo) {
    return (
      <AppShell active="mcp">
        <PublicDemoNotice
          eyebrow="Protocol workbench"
          title="MCP tool explorer"
          description="The knowledge, operations, and support MCP tools run in the full local Docker stack. The public demo shows their captured outputs inside replayed investigations instead of exposing live tool calls."
        />
      </AppShell>
    );
  }

  const catalog = await getMCPCatalog();
  const toolCount = catalog.servers.reduce((total, server) => total + server.tools.length, 0);

  return (
    <AppShell active="mcp">
      <main className="content tools-page">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Protocol workbench</p>
            <h1>MCP tool explorer</h1>
            <p>Inspect contracts and call simulated systems without involving a language model.</p>
          </div>
          <span className="queue-total">{toolCount} typed tools</span>
        </section>
        <ToolExplorer servers={catalog.servers} />
      </main>
    </AppShell>
  );
}
