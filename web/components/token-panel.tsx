"use client";

import { FormEvent, useState } from "react";
import { useAuthToken } from "./token-context";

export function TokenPanel() {
  const { token, setToken } = useAuthToken();
  const [value, setValue] = useState(token ?? "");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    setToken(trimmed.length > 0 ? trimmed : null);
  };

  const handleClear = () => {
    setValue("");
    setToken(null);
  };

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/80 p-4 shadow">
      <h2 className="text-lg font-semibold text-white">API Access Token</h2>
      <p className="mt-1 text-sm text-slate-300">
        Generate a JWT via <code className="font-mono">/api/auth/token</code> and paste it here to authorise dashboard calls.
      </p>
      <form className="mt-4 flex flex-col gap-3" onSubmit={handleSubmit}>
        <input
          className="w-full rounded border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-sm text-slate-100 focus:border-blue-400 focus:outline-none"
          placeholder="sk-..."
          value={value}
          onChange={(event) => setValue(event.target.value)}
          autoComplete="off"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            className="rounded bg-blue-500 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-400"
          >
            Save Token
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="rounded border border-slate-500 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Clear
          </button>
        </div>
      </form>
    </section>
  );
}
