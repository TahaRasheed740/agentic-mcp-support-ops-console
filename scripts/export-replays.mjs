import { readFile, writeFile } from "node:fs/promises";

const apiBase = process.env.TRACEDESK_API_URL ?? "http://localhost:8001";
const manifestPath = process.argv[2] ?? "scripts/replay-captures.json";
const outputPath = process.argv[3] ?? "apps/web/src/lib/replays.ts";

const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

const scenarios = [];
for (const item of manifest) {
  const investigation = await getJson(`/api/v1/investigations/${item.investigationId}`);
  const events = await getEvents(item.investigationId);
  if (investigation.status !== "completed") {
    throw new Error(`${item.investigationId} is ${investigation.status}, not completed.`);
  }
  scenarios.push({
    id: item.slug,
    title: item.title,
    summary: item.summary,
    caseId: investigation.case_id,
    duration: item.duration,
    tags: item.tags,
    investigation,
    events,
  });
}

const source = `import type { Investigation, InvestigationEvent } from "@/lib/api";

export type ReplayScenario = {
  id: string;
  title: string;
  summary: string;
  caseId: string;
  duration: string;
  tags: string[];
  investigation: Investigation;
  events: InvestigationEvent[];
};

// Generated from real completed local investigations by scripts/export-replays.mjs.
// Do not hand-author replay contents; re-run the exporter after capturing live runs.
export const replayScenarios: ReplayScenario[] = ${JSON.stringify(scenarios, null, 2)};

export function getReplayScenario(id: string): ReplayScenario | undefined {
  return replayScenarios.find((scenario) => scenario.id === id);
}
`;

await writeFile(outputPath, source, "utf8");
console.log(`Exported ${scenarios.length} replay scenarios to ${outputPath}`);

async function getJson(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

async function getEvents(investigationId) {
  const response = await fetch(`${apiBase}/api/v1/investigations/${investigationId}/events?after=0`);
  if (!response.ok) throw new Error(`events for ${investigationId} returned ${response.status}`);
  const text = await response.text();
  return text
    .split(/\n\n+/)
    .map((block) => block.split("\n").filter((line) => line.startsWith("data: ")))
    .filter((lines) => lines.length > 0)
    .map((lines) => JSON.parse(lines.map((line) => line.slice(6)).join("\n")));
}
