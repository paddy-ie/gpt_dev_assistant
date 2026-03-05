import { AutomationTable } from "../components/automation-table";
import { RunTable } from "../components/run-table";
import { TokenPanel } from "../components/token-panel";
import { TokenProvider } from "../components/token-context";

export default function HomePage() {
  return (
    <TokenProvider>
      <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-white">Agent3 Control Center</h1>
          <p className="max-w-2xl text-sm text-slate-300">
            Monitor autonomous coding runs, trigger automations, and keep tabs on your personal Agent3 stack. Paste a bearer token below to authenticate requests.
          </p>
        </header>
        <TokenPanel />
        <section className="grid gap-6 lg:grid-cols-2">
          <RunTable />
          <AutomationTable />
        </section>
      </main>
    </TokenProvider>
  );
}
