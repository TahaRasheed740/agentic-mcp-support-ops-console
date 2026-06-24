"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function InvestigationLaunchButton({ caseId }: { caseId: string }) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "starting" | "error">("idle");
  const [message, setMessage] = useState("");
  const [accessCode, setAccessCode] = useState("");

  async function launch() {
    setState("starting");
    setMessage("");
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (accessCode.trim()) headers["X-TraceDesk-Live-Code"] = accessCode.trim();
      const response = await fetch(`${apiUrl}/api/v1/investigations`, {
        method: "POST",
        credentials: "include",
        headers,
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

  return (
    <div className="investigation-launch">
      <label className="live-access-code">
        <span>Live access code</span>
        <input
          autoComplete="off"
          onChange={(event) => setAccessCode(event.target.value)}
          placeholder="Required on hosted demos"
          type="password"
          value={accessCode}
        />
      </label>
      <button className="investigate-button live" disabled={state === "starting"} onClick={launch} type="button">
        {state === "starting" ? "Starting..." : "Investigate with Claude"}
        <small>Read-only MCP tools</small>
      </button>
      {state === "error" && <span role="alert">{message}</span>}
    </div>
  );
}
