"use client";

import { useEffect, useState } from "react";
import type { DemoSession, Persona } from "@/lib/api";

const publicApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function PersonaSwitcher() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [session, setSession] = useState<DemoSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const [personasResponse, sessionResponse] = await Promise.all([
        fetch(`${publicApiUrl}/api/v1/personas`, { credentials: "include" }),
        fetch(`${publicApiUrl}/api/v1/sessions/current`, { credentials: "include" }),
      ]);
      if (personasResponse.ok) setPersonas((await personasResponse.json()) as Persona[]);
      if (sessionResponse.ok) setSession((await sessionResponse.json()) as DemoSession);
    }
    void load();
  }, []);

  async function choosePersona(personaId: string) {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`${publicApiUrl}/api/v1/sessions`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ persona_id: personaId }),
      });
      if (!response.ok) throw new Error("Could not start the demo session");
      setSession((await response.json()) as DemoSession);
      setMessage("Fresh workspace started");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Session request failed");
    } finally {
      setBusy(false);
    }
  }

  async function resetSession() {
    if (!session) return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`${publicApiUrl}/api/v1/sessions/${session.id}/reset`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Could not reset the workspace");
      setSession((await response.json()) as DemoSession);
      setMessage("Workspace reset");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="persona-control">
      <label htmlFor="persona-select">Working as</label>
      <select
        id="persona-select"
        value={session?.persona.id ?? ""}
        disabled={busy || personas.length === 0}
        onChange={(event) => void choosePersona(event.target.value)}
      >
        <option value="" disabled>
          Select a persona
        </option>
        {personas.map((persona) => (
          <option key={persona.id} value={persona.id}>
            {persona.name} - {persona.role}
          </option>
        ))}
      </select>
      {session && (
        <button className="text-button" type="button" disabled={busy} onClick={resetSession}>
          Reset
        </button>
      )}
      {message && <span className="session-message">{message}</span>}
    </div>
  );
}

