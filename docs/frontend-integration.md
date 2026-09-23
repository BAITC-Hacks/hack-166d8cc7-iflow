# Halyk Career Quest: frontend ↔ backend

The Halyk visual interface is the main application. It uses the FastAPI dataset,
authorization rules and persisted state. The earlier browser-only demo state is
not a source of employee skills, history or reward balances.

## Entry points and ownership

| File | Responsibility |
| --- | --- |
| `frontend/src/app/page.tsx` | Opens the connected application; the development map is the default screen |
| `frontend/src/app/hr/page.tsx` | Opens the same shell with HR selected; server authorization still applies |
| `frontend/src/app/employee/[id]/page.tsx` | Opens the shell for an employee inspection route |
| `frontend/src/components/connected-career-app.tsx` | Login, session, employee selection, overview, catalog, completion, Market and AI response UI |
| `frontend/src/components/connected-journey.tsx` | Interactive map, career-orientation selector, weekly pace, nearby steps and skill progress |
| `frontend/src/components/connected-hr.tsx` | Server aggregates, employee search, employees without candidates, JSON/CSV import |
| `frontend/src/components/artwork.tsx`, `atlas-terrain.tsx` | SVG illustrations and map landscape |
| `frontend/src/lib/api.ts` | Typed requests, authorization, timeout/cancellation and structured errors |
| `frontend/src/lib/types.ts` | Public API contracts |
| `frontend/src/lib/career-data.ts` | Presentation labels, completion choices and local selection of up to three steps |
| `frontend/src/app/globals.css`, `connected.css`, `hr-connected.css` | Halyk palette, responsive layout, states and visualizations |
| `frontend/next.config.ts` | Same-origin `/backend` proxy |

The screens inside the shell use `#roadmap`, `#home`, `#events`, `#market` and
`#hr`. Changing a hash keeps the in-memory session. A full page reload requires
login again.

## Session and access

The login screen offers two public local-demo identities:

- **Сотрудник** → `demo-active` → employee E0004.
- **HR-команда** → `demo-hr` → HR.

A password-style field accepts another token configured in
`DEV_IDENTITIES_JSON`, including `demo-employee` for E0001. These are deliberately
public development credentials, not production authentication.

Login requests `GET /api/session` and `GET /api/employees`. The server resolves
the token to a principal; the client does not infer a role from the token text.
Employee tokens can inspect only their own profile. HR can inspect employee
profiles, access aggregates and import files; HR cannot complete activities or
redeem rewards for an employee.

The token is held only in React memory. It is not placed in URLs, cookies,
`localStorage` or `sessionStorage`. Signing out destroys the workspace state.
Do not add real employee records or provider credentials to the frontend or
documentation. Provider credentials belong in backend configuration and must
never use a `NEXT_PUBLIC_*` variable.

## Request topology

```text
Browser at localhost:3000
  → /backend/api/... + Authorization: Bearer <token>
  → Next.js rewrite
  → FastAPI /api/...
  → dataset + mutable state overlay
```

| Setting | Native development | Docker Compose |
| --- | --- | --- |
| Browser origin | `http://127.0.0.1:3000` | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | `/backend` by default | `/backend` by default |
| `BACKEND_INTERNAL_URL` | `http://127.0.0.1:8000` by default | `http://backend:8000`, supplied to the frontend build |
| Persistent state | `data/state/state.json` | `career_quest_state` volume |

The browser uses the frontend origin; it does not resolve `backend` as a Docker
hostname. `NEXT_PUBLIC_API_URL` can override this topology with a direct API URL,
but then backend CORS must permit the browser's origin. Production URL settings
are build configuration; rebuild the frontend when changing them.

### Start with Docker

From the repository root:

```sh
docker compose up --build
```

Open [Career Quest](http://localhost:3000). The backend health check gates frontend
startup. Host ports are bound to loopback. Normal `docker compose down` preserves
the state volume.

### Start natively

Requires Python 3.12+ and Node.js 22+. From the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open [the native frontend](http://127.0.0.1:3000). All three public demo tokens are
included in native backend defaults. Native Python reads process environment
variables; copying `.env.example` to `.env` alone does not load them into Python.
No frontend environment file is needed for the default local proxy.

## Screens and API mapping

| Interaction | Endpoint | Result used by the UI |
| --- | --- | --- |
| Login | `GET /api/session` | Role and employee identity |
| Employee selector | `GET /api/employees` | Authorized employee summaries |
| Map, overview, catalog | `GET /api/employees/{id}/recommendations/context` | Profile, projected skills, role requirements, linked history, full catalog, candidates and exclusions |
| Confirm completion | `POST /api/employees/{id}/activities/{event_id}/complete` | Server skill changes and trajectory; context and Market reload afterwards |
| Ask AI | `POST /api/employees/{id}/recommendations` | Validated recommendations, evidence, hypotheses, questions or `no_candidates` |
| HR dashboard | `GET /api/hr/dashboard` | Skill-gap counts, participation statuses and employees without candidate events |
| HR file import | `POST /api/dataset/import` | Counts of added/unchanged records; employee list, context and HR data refresh |
| Open Market | `GET /api/market` | Catalog, own balance and redemption history; HR receives catalog without employee ledger |
| Redeem reward | `POST /api/market/redeem` | Persisted redemption receipt and resulting balance |

The profile and trajectory endpoints remain available separately. The visual
shell loads the linked recommendation context to avoid reconstructing source
catalogs or role requirements in the browser.

## What the map calculates locally

Server candidates are the eligible input set. The local planner selects at most
three events that address the currently displayed target's skill gaps, gives
critical gaps greater weight, and uses duration and event ID to resolve ties.
It projects the selected steps in memory to avoid recommending redundant gains.
These projections do not write employee progress.

Weekly pace is **1, 3 or 5 hours**. Self-paced work can span several weeks; live
events must fit within the selected weekly budget. Week labels describe workload,
not booked calendar slots. Actual live-session dates remain in the event card.
The pace is not sent to the recommendation endpoint or persisted on the backend.

The career selector switches between the next-grade requirement and an explicit
career goal already supplied by the server. It does not edit the employee's goal.
District labels and progress values come from that target's real skill gaps.
The map displays up to five relevant events; the catalog exposes the full choice.

Step explanations are rule-based and labeled as such. The separate AI panel is
the only place that displays an LLM endpoint response.

## Completion, refresh and retry

An employee can confirm a completed self-paced activity, an eligible session on
or before the application date, or an existing unfinished assignment. A future
session cannot be completed. The backend remains authoritative for eligibility,
repeat rules, dates and `gain`/`max_level` skill progression.

Completion uses a UUID `command_id` plus `source_record_id` and `session_date`.
The frontend keeps the same command for a retry after an uncertain response
during the page session. The server persists the original receipt and rejects
reuse with different content. After success, the UI reloads context and Market
instead of treating a local animation as a saved completion.

Reads use cancellation and current-selection guards. Switching profile,
changing the inspected employee or leaving HR prevents stale responses from
overwriting the new screen. Loading, empty states, server errors and retry
actions are exposed in the UI. The API client applies a request timeout and
preserves structured validation details.

## Market ledger

Market is a working demonstration ledger backed by the same JSON state overlay
as progress. A clean state begins with **0 coins**. Each new voluntary runtime
completion earns **80 coins**. Mandatory events earn none; original and imported
historical completions also earn none.

Current server catalog:

| Reward | Coins |
| --- | --- |
| Книга для следующего шага | 80 |
| Термокружка Halyk | 160 |
| Шоппер Halyk | 240 |
| Билет на конференцию | 400 |

Redemption accepts `command_id` and `reward_id`. The backend checks the employee,
reward, balance and prior redemption under the shared mutation lock. Each reward
can be redeemed once per employee. A retried command returns its original
receipt; insufficient balance or a second redemption is rejected. Ledger receipts
are validated at startup and survive normal restarts.

Coins do not change skills, grades or access to learning. The UI identifies
rewards as demonstrations: no money is charged, no real delivery is triggered,
and there is no commercial Halyk Market integration.

## HR and imports

The dashboard shows real aggregate values:

- Top skill gaps by number of employees below the next-grade requirement.
- Participation totals and status breakdowns, including a per-event table.
- Searchable employee list and links to inspect each employee's map.
- Employees with no eligible catalog candidates.

Participation counts are records, not unique people. One person can contribute
multiple participations. `employees_without_recommendation` is currently `null`;
the UI explicitly labels the AI-coverage metric unavailable and does not present
the candidate count as AI recommendation coverage.

Imports accept `employees.json` with the original envelope and/or
`activity_history.csv` with the original columns. Multipart fields are
`employees` and `history`; the server's total limit is 10 MiB including multipart
overhead. Errors display the server message and exact sanitized location details.
Successful imports show added/unchanged counts and refresh the parent data.
Existing atomic validation and append/no-op/conflict semantics are unchanged.

## AI integration boundary

The UI calls the real recommendation endpoint and can render recommendations,
their factors, clearly marked hypotheses and clarifying questions. Response
employee identity, revision and application date must match the current context.
The interface asks for a fresh request if those inputs have changed.

OpenAI Responses is configured through the root `.env` (`AI_PROVIDER=openai`, `OPENAI_API_KEY`). See [provider setup](openai-provider.md). Missing credentials return 501; no candidates requires no model call. The map displays only the saved AI selection, with no rule-based filler nodes. Weekly pace changes duration estimates only. Saving answers to clarification questions is still pending.

## Remaining work and validation status

- Extend live model evaluations and meet the end-to-end latency target.
- Add write contracts for profile/career-goal editing, event enrollment and
  answers to clarification questions.
- Populate HR recommendation-coverage metrics when the provider workflow exists.
- Add production authentication before any deployment beyond the local demo.

For this integration, `npm --prefix frontend run build` completed successfully:
Next.js webpack compilation, TypeScript checks and static-page generation passed.
Backend Uvicorn startup with the dataset also completed. Unit tests and browser
tests were not run; no end-to-end validation is claimed. Optional verification
commands remain in the root README; the foundation's earlier validation record
is in [handoff.md](handoff.md).
