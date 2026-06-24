"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { RuntimeCapabilities } from "@/lib/api";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function InvestigationLaunchButton({
  caseId,
  runtime,
}: {
  caseId: string;
  runtime: RuntimeCapabilities;
}) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "starting" | "error">("idle");
  const [message, setMessage] = useState("");

  async function launch() {
    setState("starting");
    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/investigations`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });
      const body = (await response.json()) as { id?: string; detail?: string };
      if (!response.ok || !body.id) throw new Error(body.detail ?? "Unable to start investigation");
      router.push(`/investigations/${body.id}`);
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Unable to start investigation");
    }
  }

  if (!runtime.live_investigations_enabled) {
    return (
      <div className="investigation-launch replay-only-launch">
        <button className="investigate-button" disabled type="button">
          Live Claude disabled
          <small>Replay-only public demo</small>
        </button>
        <p>{runtime.live_investigations_reason}</p>
        <Link href="/replays">Open recorded replays</Link>
      </div>
    );
  }

  return (
    <div className="investigation-launch">
      <button className="investigate-button live" disabled={state === "starting"} onClick={launch} type="button">
        {state === "starting" ? "Starting..." : "Investigate with Claude"}
        <small>Read-only MCP tools</small>
      </button>
      {state === "error" && <span role="alert">{message}</span>}
    </div>
  );
}
