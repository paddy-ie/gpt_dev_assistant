# Agent3 Personal Stack

Self-hosted clone of Replit Agent3: a FastAPI backend orchestrating autonomous coding runs, an automation engine for workflow bots, a real-time telemetry feed, and a Next.js control center.

## Highlights
- **Autonomous runs** - Queue repo tasks, follow plan/execution/test phases, and stream live events via REST or WebSocket.
- **Automation factory** - Versioned automations with run history, a stub execution engine, and CLI helpers to trigger flows.
- **Real-time telemetry** - Run events persist to SQLite and broadcast over `/api/ws/runs/{id}` for dashboards or mobile monitoring.
- **Web dashboard** - React/Next.js UI shows run and automation status once you paste an auth token.
- **Dev tooling** - Typer-based CLI and cross-platform scripts to launch backend and frontend quickly.

## Repository Layout
```
backend/        # FastAPI app, orchestrators, services, CLI
web/            # Next.js dashboard (Next 14 + Tailwind + SWR)
scripts/        # Helper scripts for dev servers (PowerShell/Bash)
docs/           # Architecture plan and design notes
api/, frontend/, etc. # Legacy Flask IDE (kept for reference)
```

## Backend API
1. Install deps & run migrations (SQLite by default):
   ```bash
   cd backend
   python -m venv .venv && .venv/Scripts/Activate.ps1  # or source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   or run `scripts/dev_backend.ps1` / `scripts/dev_backend.sh` after activating your venv.
2. Configure `.env` (see `backend/.env.example`):
   - `AGENT3_SECRET_KEY` - JWT signing secret.
   - `AGENT3_DATABASE_URL` - async database URL (ex. `sqlite+aiosqlite:///./agent3.db`).
   - `AGENT3_ALLOWED_ORIGINS` - comma list for CORS.
3. Visit `http://127.0.0.1:8000/docs` for OpenAPI.

Key endpoints:
- `POST /api/auth/register` - create user, then `POST /api/auth/token` for JWTs.
- `POST /api/runs` - enqueue repo automation (auto-starts orchestrator).
- `GET /api/runs/{id}/events?after=42` - poll incremental telemetry.
- `ws://127.0.0.1:8000/api/ws/runs/{id}?token=...` - live event stream.
- `POST /api/automations` / `PATCH` / `POST /publish` - manage automation lifecycle.
- `POST /api/automations/{id}/runs` - queue automation executions (processed by stub runner).

## IDE Assistant
- REST endpoints (`POST /api/assistant/chat`, `GET /api/assistant/history`, `POST /api/assistant/history/clear`) are now served by FastAPI and mirrored in the legacy Flask IDE for backwards compatibility.
- Configure models through environment variables:
  - `IDE_ASSISTANT_PROVIDER` (`openai` default, `codex` available).
  - `IDE_ASSISTANT_MODEL` (shared fallback for all providers).
  - `OPENAI_API_KEY` / `OPENAI_ASSISTANT_MODEL` for OpenAI-backed runs.
  - `CODEX_API_BASE`, `CODEX_API_KEY`, and optional `CODEX_ASSISTANT_MODEL` for Codex.
- Override per request by passing `model` values like `codex:my-model` or `openai:gpt-4.1-mini`; omit the suffix to use provider defaults.
- Responses bubble usage metadata when providers supply it, enabling future dashboards to compare model cost/latency.

## Automation Runner
- Queue stored in `AutomationRunner`; runs execute immediately when automation state is `LIVE`.
- Each run persists to `automation_runs` with status, timestamps, output JSON, and error message.
- Extend `app/automations/runner.py` to call real toolchains or external services.

## CLI Skeleton
```
cd backend
python cli.py automations list --token <JWT>
python cli.py automations trigger 1 --token <JWT>
python cli.py runs list --token <JWT>
```
Environment variables: set `AGENT3_API_URL` (default `http://127.0.0.1:8000/api`) and `AGENT3_ACCESS_TOKEN` to avoid supplying `--token` each time.

## Dashboard (Next.js)
1. `cd web`
2. `npm install`
3. `npm run dev` (or `scripts/dev_frontend.ps1` / `scripts/dev_frontend.sh`)
4. Open `http://127.0.0.1:3000`, paste a JWT token in the panel, and watch runs and automations refresh live.

Configuration:
- `NEXT_PUBLIC_API_BASE` (default `http://127.0.0.1:8000/api`) points at the backend.
- Tailwind styles live in `app/globals.css`.

## Telemetry
- `RunService.append_event` pushes to the in-memory `TelemetryHub` that powers WebSocket clients.
- Extend `app/telemetry/hub.py` if you want Redis/NATS backing or external sinks.

## Dev Scripts
- `scripts/dev_backend.ps1|sh` - Run backend with Uvicorn.
- `scripts/dev_frontend.ps1|sh` - Run Next.js dev server.
- `backend/main.py` - Uvicorn entry for production (`python backend/main.py`).

## Next Steps
- Swap stub orchestrators for real containerized execution.
- Wire integrations (Slack/Telegram/Email/Notion) using connectors under `integrations/`.
- Harden auth (refresh tokens, scopes) and add run metrics dashboards.
- Expand CLI with login flow and automation inspection commands.
