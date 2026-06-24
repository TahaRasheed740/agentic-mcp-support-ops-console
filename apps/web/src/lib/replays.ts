import type { Investigation, InvestigationEvent } from "@/lib/api";

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

export const replayScenarios: ReplayScenario[] = [];

export function getReplayScenario(id: string): ReplayScenario | undefined {
  return replayScenarios.find((scenario) => scenario.id === id);
}
