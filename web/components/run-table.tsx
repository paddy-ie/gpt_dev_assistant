"use client";

import useSWR from "swr";
import { apiFetch } from "../lib/api";
import { useAuthToken } from "./token-context";

export type Run = {
  id: number;
  repo_label: string;
  goal: string;
  status: string;
  created_at: string;
  updated_at: string;
};

const statusClasses: Record<string, string> = {
  pending: "bg-slate-700 text-slate-200",
  planning: "bg-blue-500/80 text-white",
  executing: "bg-amber-500/80 text-black",
  testing: "bg-purple-500/80 text-white",
  completed: "bg-emerald-500/80 text-black",
  failed: "bg-rose-500/80 text-white",
  cancelled: "bg-slate-500/80 text-white",
  stalled: "bg-orange-500/80 text-black",
};

export function RunTable() {
  const { token } = useAuthToken();

  const { data, error, isValidating, mutate } = useSWR(token ? ["/runs", token] : null, ([path, tk]) => apiFetch<Run[]>(path, tk), {
    refreshInterval: 15000,
  });

  if (!token) {
    return <p className="text-sm text-slate-300">Set a token to load recent runs.</p>;
  }

  if (error) {
    return (
      <div className="rounded border border-rose-700 bg-rose-950/60 p-3 text-sm">
        Failed to load runs: {error.message}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 shadow">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Recent Coding Runs</h2>
        <button
          onClick={() => mutate()}
          className="rounded border border-slate-500 px-3 py-1 text-xs uppercase tracking-wide text-slate-200 hover:bg-slate-800"
        >
          Refresh{isValidating ? "?" : ""}
        </button>
      </div>
      <table className="mt-4 w-full text-left text-sm">
        <thead className="text-slate-300">
          <tr>
            <th className="py-2">ID</th>
            <th className="py-2">Repo</th>
            <th className="py-2">Status</th>
            <th className="py-2">Goal</th>
            <th className="py-2">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700 text-slate-200">
          {data?.map((run) => (
            <tr key={run.id}>
              <td className="py-2 font-mono text-xs">#{run.id}</td>
              <td className="py-2">{run.repo_label}</td>
              <td className="py-2">
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ${statusClasses[run.status] ?? "bg-slate-700 text-slate-200"}`}>
                  {run.status.toUpperCase()}
                </span>
              </td>
              <td className="py-2 text-slate-300">{run.goal}</td>
              <td className="py-2 text-xs text-slate-400">{new Date(run.updated_at).toLocaleString()}</td>
            </tr>
          ))}
          {data && data.length === 0 && (
            <tr>
              <td className="py-4 text-center text-slate-400" colSpan={5}>
                No runs yet. Create a run from the IDE or API to see it here.
              </td>
            </tr>
          )}
          {!data && (
            <tr>
              <td className="py-4 text-center text-slate-400" colSpan={5}>
                Loading runs?
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
