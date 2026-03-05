"use client";

import { useState } from "react";
import useSWR from "swr";
import { apiFetch } from "../lib/api";
import { useAuthToken } from "./token-context";

export type Automation = {
  id: number;
  name: string;
  description: string;
  state: string;
  version: number;
  updated_at: string;
};

const stateColors: Record<string, string> = {
  draft: "bg-slate-700 text-slate-200",
  generated: "bg-indigo-500/80 text-white",
  testing: "bg-amber-500/80 text-black",
  live: "bg-emerald-500/80 text-black",
  paused: "bg-slate-500/80 text-white",
  retired: "bg-slate-600/80 text-white",
};

export function AutomationTable() {
  const { token } = useAuthToken();
  const [message, setMessage] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState<number | null>(null);

  const { data, error, isValidating, mutate } = useSWR(
    token ? ["/automations", token] : null,
    ([path, tk]) => apiFetch<Automation[]>(path, tk),
    { refreshInterval: 20000 }
  );

  if (!token) {
    return <p className="text-sm text-slate-300">Provide a token to inspect automations.</p>;
  }

  const triggerAutomation = async (automationId: number) => {
    try {
      setIsTriggering(automationId);
      setMessage(null);
      await apiFetch(`/automations/${automationId}/runs`, token, { method: "POST", body: JSON.stringify({}) });
      setMessage(`Automation ${automationId} queued`);
      mutate();
    } catch (err) {
      if (err instanceof Error) {
        setMessage(`Failed to trigger: ${err.message}`);
      }
    } finally {
      setIsTriggering(null);
    }
  };

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 shadow">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Automation Catalog</h2>
        <button
          onClick={() => mutate()}
          className="rounded border border-slate-500 px-3 py-1 text-xs uppercase tracking-wide text-slate-200 hover:bg-slate-800"
        >
          Refresh{isValidating ? "?" : ""}
        </button>
      </div>
      {message && <p className="mt-2 text-sm text-slate-300">{message}</p>}
      {error && (
        <div className="mt-3 rounded border border-rose-700 bg-rose-950/60 p-3 text-sm">
          Failed to load automations: {error.message}
        </div>
      )}
      <div className="mt-4 grid gap-3">
        {data?.map((automation) => (
          <div key={automation.id} className="rounded border border-slate-700 bg-slate-900/90 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-semibold text-white">{automation.name}</h3>
                <p className="text-sm text-slate-300">{automation.description || "No description"}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${stateColors[automation.state] ?? "bg-slate-700 text-slate-200"}`}>
                {automation.state.toUpperCase()} ? v{automation.version}
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
              <span>Updated {new Date(automation.updated_at).toLocaleString()}</span>
              <button
                onClick={() => triggerAutomation(automation.id)}
                disabled={isTriggering === automation.id}
                className="rounded bg-blue-500 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-blue-900"
              >
                {isTriggering === automation.id ? "Queuing?" : "Trigger Run"}
              </button>
            </div>
          </div>
        ))}
        {data && data.length === 0 && (
          <div className="rounded border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-300">
            No automations defined yet.
          </div>
        )}
        {!data && !error && (
          <div className="rounded border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-300">
            Loading automations?
          </div>
        )}
      </div>
    </div>
  );
}
