import Link from "next/link";
import type { ReactNode } from "react";
import { PersonaSwitcher } from "./persona-switcher";

export function AppShell({
  children,
  active = "queue",
}: {
  children: ReactNode;
  active?: "queue" | "investigation" | "knowledge" | "mcp" | "replays" | "evaluations";
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="TraceDesk support queue">
          <span className="brand-mark">T</span>
          <span>
            TraceDesk
            <small>Acme Automations</small>
          </span>
        </Link>
        <nav className="side-nav" aria-label="Primary navigation">
          <Link className={`nav-item ${active === "queue" ? "active" : ""}`} href="/">
            <span className="nav-glyph">Q</span>Support queue
          </Link>
          <Link className={`nav-item ${active === "investigation" ? "active" : ""}`} href="/investigations">
            <span className="nav-glyph">I</span>Investigations
          </Link>
          <Link className={`nav-item ${active === "replays" ? "active" : ""}`} href="/replays">
            <span className="nav-glyph">R</span>Replays
          </Link>
          <Link className={`nav-item ${active === "knowledge" ? "active" : ""}`} href="/knowledge">
            <span className="nav-glyph">K</span>Knowledge
          </Link>
          <Link className={`nav-item ${active === "mcp" ? "active" : ""}`} href="/tools">
            <span className="nav-glyph">M</span>MCP tools
          </Link>
          <Link className={`nav-item ${active === "evaluations" ? "active" : ""}`} href="/evaluations">
            <span className="nav-glyph">E</span>Evaluations
          </Link>
        </nav>
        <div className="iteration-card">
          <span>Iteration 7</span>
          <strong>Evaluation hardening</strong>
          <p>Reports track evidence recall, citation validity, diagnosis quality, and write safety.</p>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="environment"><span />Demo environment</div>
          <PersonaSwitcher />
        </header>
        {children}
      </div>
    </div>
  );
}
