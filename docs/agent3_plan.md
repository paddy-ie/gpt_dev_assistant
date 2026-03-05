# Agent3-Style Personal System Plan

## 1. Scope & Assumptions
- **Primary goal**: self-hosted autonomous coding & automation platform mirroring Replit Agent3 capabilities for a single advanced user (expandable to small team later).
- **Key capabilities to replicate**:
  - Autonomous coding runs up to ~200 minutes with llm-driven planning, execution, testing loops.
  - Live monitoring (web & mobile-friendly) with ability to inspect logs, diffs, progress.
  - Agent generation: user can define automations/workflows that target integrations (Slack, email, Telegram, Notion) via natural language prompts.
  - Deployment of generated agents/bots with minimal manual wiring.
- **Operating constraints**:
  - Runs on personal infrastructure (single beefy workstation or small cloud server) initially.
  - Reuse open-source LLMs by default (hosted API fallback for premium models); must abstract model provider.
  - Prefer Python for orchestration/backend to align with existing repo & ecosystem; TypeScript/React for UI.
  - Containerized execution for untrusted code; rely on Docker/Podman available on host.
- **Non-goals (initial)**:
  - Multi-tenant SaaS hardening (focus on single-user security model, soft multi-user later).
  - Marketplace / billing flows.
  - Voice or AR interfaces.
  - Auto-scaling across cluster (design for eventual expansion but not initial deliverable).
- **Tech stack assumptions**:
  - Backend: FastAPI (Python 3.12), SQLModel/SQLAlchemy with Postgres (development may use SQLite), Celery/RQ with Redis for async jobs.
  - Orchestration worker: Python, uses docker-py for container control, GitPython for repo ops, pytest/pytest-xdist for testing.
  - LLM provider abstraction: OpenAI-compatible client, optional local (Ollama) via REST, guardrails for token budgets. Registry already ships with OpenAI + Codex adapters keyed off `IDE_ASSISTANT_PROVIDER`.
  - Frontend: Next.js 15 (React 19) with Tailwind; mobile web responsive layout.
  - Realtime updates: WebSocket (FastAPI + WebSocket) and fallback Server-Sent Events.
  - Secrets/Config: Dotenv in dev, Vault integration optional later.
## 2. Core Coding Agent MVP
- **High-level components**:
  - `RunOrchestrator` service (FastAPI) exposes REST endpoints to create runs, fetch status, stream logs.
  - `Planner` module turns natural-language tasks into ordered plans (tree of steps) using structured prompting and tool-context (repo map, tests, dependencies).
  - `Executor` worker (Celery task) pulls plan steps, manages sandboxed repo checkout, applies changes via tool adapters (filesystem, git, package manager).
  - `ReflectionEngine` triggers targeted tests/lints after each significant change, feeds outputs back into the planner for adjustments.
  - `ArtifactStore` persists run metadata (DB), code snapshots (Git branches + object storage), logs (OpenTelemetry + Loki/SQLite fallback).
- **Run lifecycle**:
  1. User submits prompt + repo target + constraints (max tokens, runtime, test focus).
  2. Planner fetches repo summary (cached embeddings, LOC, key files) and generates initial high-level steps.
  3. `PlanRefiner` iteratively expands steps into executable actions (edit file, run command, open PR) with ranked priorities.
  4. Executor spins an isolated container (bind mount repo) and sequentially executes actions; uses structured tool outputs to update state.
  5. After code edits, ReflectionEngine selects appropriate validation suite (unit tests, lint, e2e) and runs inside sandbox.
  6. Failures feed back into planner with error summaries to generate remediation steps; success criteria mark step complete.
  7. Run terminates when all plan steps satisfy success signals or runtime/token budget reached; final artifacts (diff, logs, tests) stored.
- **Planner architecture**:
  - Prompt pipeline uses ReAct-style loops with guardrails: `context builder` -> `task decomposer` -> `action decision`.
  - Maintains run memory in Postgres JSONB: list of facts, TODOs, blocked issues.
  - Employs heuristics to limit churn (freeze files after N consecutive failures, escalate to user hint).
- **Execution sandbox**:
  - `docker-compose` template with language-specific images (Python, Node, Go). Uses ephemeral container per run; caches dependencies via shared volume.
  - File edits performed through patch application (unified diff) to enable deterministic diffs and revert.
  - Commands executed with timeout + resource caps (CPU quota, memory limit) derived from run SLA.
- **State model**:
  - `runs` table: id, repo_id, goal text, status enum (pending/planning/executing/testing/completed/failed/cancelled), token_usage, started_at, finished_at.
  - `steps` table: id, run_id, parent_id, type (plan/edit/test/deploy), status, summary, llm_input/reflection fields.
  - `artifacts` table: id, run_id, type (log, diff, test_report, preview_url), storage_url/inline blob hashed.
  - `events` stream: append-only log for realtime UI (status changes, new output chunks).
- **LLM prompt data sources**:
  - Repo summary (tree + top embeddings stored via pgvector) to reduce full file reads.
  - Tool wiki (YAML describing commands, exit codes) to let model choose best actions.
  - Test heuristics catalogue to match modules to correct test suite.
- **Extensibility hooks**:
  - Tools registry interface so new actions (e.g., `terraform_apply`, `db_migrate`) can be plugged in with schema.
  - Policy engine for guardrails (regex forbid secrets, ensure tests pass before finalizing).
  - Observability via OpenTelemetry instrumentation around planner/executor loops.
## 3. Monitoring & Telemetry
- **Objectives**:
  - Provide second-by-second visibility into agent runs (status, current step, command output, diffs).
  - Support responsive web dashboard + mobile PWA with push notifications.
  - Persist observability data for post-mortem analysis.
- **Backend services**:
  - `TelemetryService` (FastAPI) exposes GraphQL subscription or REST + WebSocket for run timelines.
  - Uses Redis Streams (or NATS) as central event bus; executor publishes structured events (`stdout`, `stderr`, `metric`, `heartbeat`, `plan_update`).
  - Events mirrored to Postgres `run_events` table for long-term storage (batched async worker).
  - OpenTelemetry collector receives traces/metrics; exporters to Tempo/Prometheus (optional) or lightweight SQLite-based store for personal deployment.
- **Event schema**:
  - `RunEvent`: {id, run_id, step_id?, type, level, message, payload_json, ts}.
  - Chunk large outputs with sequence numbers; mark final to signal UI to stop streaming.
  - Heartbeat event every 30s from executor with container resource usage (CPU%, RSS, IO) captured via cgroups.
- **Live Monitoring UI**:
  - React dashboard with panels: timeline, command log, diff viewer, resource gauges.
  - Mobile layout collapses into tabbed interface (status, logs, artifacts).
  - Web push (via service worker) triggers on step state change or failure.
  - Provide "nudge" capability: user can send hint/override to run (UI posts to `/runs/{id}/hint`).
- **Alerting & notifications**:
  - Notification service integrates with email/Slack DM (depending on configured channels) to announce completion/failure.
  - Configurable thresholds for long-running steps; if no heartbeat > 2 minutes, send alert + auto-mark run as stalled.
- **Historical analytics**:
  - Weekly summary job aggregates run durations, success rates, top failing tests; stored in `run_metrics` table for trend charts.
  - Optionally export sanitized runs to Notion/Markdown for knowledge base.
- **Security considerations**:
  - WebSocket tokens scoped per run; signed short-lived JWT delivered via REST once user authenticates.
  - Telemetry payload scrubbed for secrets using regex + entropy filters before broadcasting.
## 4. Agent Factory & Workflow Management
- **Goals**:
  - Convert natural-language intents into reusable automations ("agents") that can be scheduled or triggered by external channels.
  - Maintain catalog with versioning, environment config, deployment metadata.
- **Prompt-to-agent pipeline**:
  1. User describes desired automation (inputs, outputs, target integration) via UI.
  2. `SpecExtractor` LLM prompt converts description into structured schema: triggers, actions, data sources, integration requirements.
  3. `Validator` runs deterministic checks (available connectors, auth scopes, rate limits) and requests clarification if gaps.
  4. `WorkflowSynthesizer` produces executable workflow graph using internal DSL (YAML/JSON) describing tasks, conditionals, retries.
  5. User reviews plan, edits via visual builder (nodes/edges) or JSON editor, then clicks "Generate" to instantiate automation code.
- **Workflow representation**:
  - Use `Temporal`-style state machine expressed in `workflow.yaml` with nodes:
    - `trigger` (cron, webhook, manual, integration event)
    - `task` (llm_action, http_request, db_query, code_snippet, agent_run)
    - `branch` (condition), `loop`, `parallel` groups
  - Store canonical version in Postgres `automations` table (id, name, version, status, config_json, created_by, last_run_at).
  - Generated runtime code stored in Git repo under `automations/<name>/<version>/` with metadata.
- **Execution engine**:
  - Reuse Celery workers with dedicated queue `automation`. Worker interprets workflow graph and dispatches tasks.
  - Provide sandboxed `llm_action` step to call coding agent for sub-tasks (recursive agent generation).
  - Integrate secrets via hashed references (workflow only stores pointer to secret, not raw value).
- **UI builder**:
  - React Flow-based canvas: nodes for triggers/actions; side panel to edit parameters.
  - Inline test mode to simulate run using sample inputs, capturing logs.
  - Version diff viewer to compare YAML between versions; allow rollback and stage/publish states.
- **Lifecycle management**:
  - States: `draft` -> `generated` -> `testing` -> `live` -> `paused` -> `retired`.
  - Add scheduler service to handle cron triggers (APScheduler) and event router for webhooks (FastAPI endpoints mapping to automations).
  - Provide `DeploymentManifest` describing target environment, secrets, integration tokens so agent can deploy to Slack/Telegram etc.
- **Governance & safety**:
  - Rate limiting per automation to avoid runaway loops.
  - Audit log of edits: `automation_audit` table capturing diff, editor, timestamp.
  - Static analyzers for generated code to ensure safe imports, restricted network access if needed.
## 5. Integration Strategy & Deployment
- **Connector architecture**:
  - Standardize on `IntegrationAdapter` interface (connect, validate_credentials, send, receive, revoke).
  - Maintain catalog in `integrations/registry.yaml` with scopes, rate limits, event types.
  - Use background workers to process outbound messages; inbound webhooks hit FastAPI endpoints, validated via HMAC/signature.
- **Slack**:
  - App client using Bolt for Python; support slash commands, message buttons, event subscriptions.
  - OAuth 2.0 install flow through frontend; tokens stored encrypted (Fernet + user master key).
  - Deploy interactive flows by mapping Slack actions to automation triggers (e.g., `/agent run <goal>`).
- **Telegram**:
  - Bot API via python-telegram-bot; uses webhook mode (reverse proxy via Caddy/NGINX) or polling fallback.
  - Templates for common automations (booking, FAQ) generated by workflow engine.
  - Rate limiting + conversation state stored in Redis (per chat id).
- **Email**:
  - SMTP relay (e.g., Mailgun/Sendgrid) for outbound; IMAP listener or inbound parse webhook for responses.
  - Provide templating via Jinja2 with test harness; track deliveries in `messages` table.
- **Notion**:
  - Official Notion API: create/update pages & databases, append blocks.
  - Use integration token stored as secret; schema introspection cached for builder to offer property pickers.
  - Support pushing run summaries and automation reports into Notion workspace.
- **Additional targets**:
  - Webhooks (generic HTTP) for extensibility.
  - Local scripts via CLI runner for offline tasks.
- **Deployment story**:
  - `docker-compose` stack: `api`, `worker`, `scheduler`, `redis`, `postgres`, `otel-collector`, `frontend`, optional `nginx`.
  - Provide `make deploy` to generate env files, run migrations, seed default admin user.
  - CI workflow (GitHub Actions) runs tests, builds containers, pushes to registry; personal user can run `make release` to upgrade.
- **Secrets management**:
  - Use `doppler`/`envdir` optional; default to `.env` with AES-encrypted secret values (command `manage.py secrets set`).
  - Integration tokens rotated via scheduled reminders + UI view.
- **Compliance**:
  - Log consent for integrations; keep audit of outbound messages for traceability.
## 6. Hardening, QA, & Roadmap
- **Security posture**:
  - Authentication: self-hosted Auth via FastAPI + JWT, optional SSO (OIDC). Support hardware key (WebAuthn) later.
  - Authorization: simple RBAC (owner, collaborator, viewer). Guard automation edits behind owner role.
  - Secrets hygiene: encrypt at rest, redact in logs, enforce least privilege for integration scopes.
  - Container sandbox: seccomp/apparmor profiles, readonly root FS, allowlist outbound domains.
  - Supply chain: pin dependencies, enable Dependabot + `pip-audit`/`npm audit` in CI.
- **Reliability & resilience**:
  - Graceful resume: persist run state every step; restart worker can pick up from last completed step.
  - Backpressure: limit concurrent runs via semaphore; queue additional tasks.
  - Snapshotting: automatic git commit per successful run in `agent_runs/<timestamp>` branch; optional PR generation.
  - Backups: nightly Postgres dump + object store sync (rclone) with retention.
- **Testing strategy**:
  - Unit tests for planner utilities, workflow parser, integration adapters (use pytest + fixtures).
  - Integration tests using docker-compose in CI to spin entire stack; run sample run to completion.
  - End-to-end smoke test triggered post-deploy (GitHub Actions) verifying run creation, telemetry streaming, Slack notification simulation.
  - Chaos tests (manual initially) to kill worker mid-run and ensure resume.
  - Prompt regression suite: store canonical prompts/responses to detect drift when upgrading models.
- **Rollout roadmap**:
  1. **Phase 0 - Foundations (Week 1-2)**: Set up repo structure, infrastructure-as-code, baseline FastAPI + Postgres + Redis + Next.js skeleton. Implement auth + basic run CRUD.
  2. **Phase 1 - Agent MVP (Week 3-6)**: Build planner/executor/test loop for single language (Python), container sandbox, git diff artifacts, minimal UI console.
  3. **Phase 2 - Monitoring (Week 7-8)**: Add telemetry service, WebSocket streaming, mobile-friendly dashboard, push notifications.
  4. **Phase 3 - Agent Factory (Week 9-11)**: Introduce workflow DSL, builder UI, scheduler, automation execution engine.
  5. **Phase 4 - Integrations (Week 12-13)**: Ship Slack + email connectors, wire automations to run via triggers, add secrets manager.
  6. **Phase 5 - Polish & Hardening (Week 14-16)**: Expand language support (Node), add Telegram/Notion connectors, security review, documentation, auto-updater scripts.
- **Documentation & DX**:
  - Maintain `docs/` with architecture, API reference, runbooks.
  - Provide CLI (`agent3ctl`) for managing runs, automations, secrets.
  - Include sample automations + tutorial walkthrough mirroring Replit marketing demos.
