# Career Quest: initial application architecture

Date: 2026-09-23

Status: proposed written spec, awaiting user approval. No product implementation is authorized by this document alone.

## 1. Purpose, sources and scope

Build the initial foundation for Case 1 only: a Next.js application backed by FastAPI, the real starter-kit schemas, deterministic employee development calculations, lightweight backend authorization, and immutable source data with durable local state. The intended users are employees viewing their own development and HR inspecting development information and importing jury data.

The source requirements and dataset observations are recorded in [discovery.md](../../discovery.md). The local hackathon PDF and starter-kit README are authoritative for requirements and data semantics. The primary Drive URL could not be independently read. The user approved the discovery baseline and architectural direction and clarified authorization and collision rules. The unavailable grill-with-docs skill was not used; the user explicitly removed it as a blocker. The older workflow-blocker text in discovery.md is historical and superseded by this approval.

This milestone implements data loading, validated contracts, current-skill projection, gaps, eligibility, trajectory, completion, import, basic HR aggregates, and a minimal frontend. It defines but does not implement AI ranking or explanations. It must not be described as a finished hackathon submission: the final case requires actual explainable AI recommendations with at least three factors and 1–3 recommended steps.

Success means the real dataset loads, authorization is enforced in the API, deterministic state changes survive restart without modifying raw files, frontend and backend start together, and the documented checks pass. Optional gamification, localization, enterprise authentication and integrations are excluded.

## 2. Architecture and choices

```text
Next.js pages/components -> lib/api.ts -> FastAPI routes/dependencies
                                            |
                                         Services
                                            |
                                       Repositories
                                            |
                          immutable JSON/CSV + mutable JSON state
```

Use the existing repository root, with separate frontend and backend projects. Concrete repositories and a small snapshot container are enough; do not introduce a generic repository framework, event bus, database, cache service or agent framework.

Chosen persistence: one file-backed overlay plus an in-memory validated snapshot. A purely in-memory overlay would lose jury imports and completions on restart. A database would add infrastructure without solving a requirement at this dataset size. The file approach requires exactly one backend process/worker and serialized mutations; these limits are explicit.

Differences from the suggested tree serve concrete responsibilities: add auth and shared API dependencies, dataset/state contracts and repositories, an eligibility service, and dataset/completion orchestration. Omit unused hooks and speculative AI prompt/explanation files. Add those only when they have implementations. Keep new application API fields separate from source schemas.

## 3. Planned final repository tree

This is the implementation target, not a claim these files already exist. Python package directories also contain __init__.py files.

```text
.
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── globals.css
│   │   │   ├── page.tsx
│   │   │   ├── employee/[id]/page.tsx
│   │   │   └── hr/page.tsx
│   │   ├── components/
│   │   │   ├── session-provider.tsx
│   │   │   ├── employee/profile.tsx
│   │   │   ├── employee/trajectory.tsx
│   │   │   ├── hr/dashboard.tsx
│   │   │   └── ui/status-message.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── next-env.d.ts
│   ├── next.config.ts
│   ├── postcss.config.mjs
│   ├── .dockerignore
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── employees.py
│   │   │   ├── recommendations.py
│   │   │   ├── activities.py
│   │   │   ├── hr.py
│   │   │   └── dataset.py
│   │   ├── schemas/
│   │   │   ├── employee.py
│   │   │   ├── skill.py
│   │   │   ├── activity.py
│   │   │   ├── history.py
│   │   │   ├── recommendation.py
│   │   │   ├── dataset.py
│   │   │   ├── state.py
│   │   │   └── responses.py
│   │   ├── repositories/
│   │   │   ├── employees.py
│   │   │   ├── events.py
│   │   │   ├── skills.py
│   │   │   ├── history.py
│   │   │   ├── dataset.py
│   │   │   └── state.py
│   │   ├── services/
│   │   │   ├── skill_gap.py
│   │   │   ├── trajectory.py
│   │   │   ├── eligibility.py
│   │   │   ├── progress_engine.py
│   │   │   ├── completion.py
│   │   │   ├── dataset.py
│   │   │   ├── hr.py
│   │   │   └── recommendation_engine.py
│   │   ├── ai/
│   │   │   ├── client.py
│   │   │   └── recommender.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── auth.py
│   │       └── errors.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_data_loading.py
│   │   ├── test_skill_gap.py
│   │   ├── test_progress.py
│   │   ├── test_eligibility.py
│   │   ├── test_import.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .dockerignore
│   └── Dockerfile
├── data/
│   ├── raw/
│   │   ├── employees.json
│   │   ├── events.json
│   │   ├── skills.json
│   │   ├── activity_history.csv
│   │   ├── README.md
│   │   ├── README.kz.md
│   │   └── README.ru.md
│   ├── fixtures/README.md
│   └── state/                         # generated locally; ignored by Git
├── docs/
│   ├── discovery.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── handoff.md
│   └── superpowers/
│       ├── specs/2026-09-23-career-quest-design.md
│       └── plans/                     # written after spec approval
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

Raw starter-kit files are copied byte-for-byte from the archive, excluding macOS metadata. No public upload of the dataset is part of this work; the specification restricts it to the hackathon. Fixture documentation explains tiny synthetic test data, and tests use temporary mutable-state directories.

## 4. Backend boundaries and domain models

main.py is the composition root: configure the app, load and validate data in lifespan startup, assemble repositories/services, install error handling and CORS, and register routes. Routes parse HTTP inputs and delegate. FastAPI dependencies resolve the principal, enforce access and provide a consistent dataset snapshot. Services do not open files or depend on HTTP exceptions.

Pydantic source models preserve starter-kit names and envelopes:

| Model | Fields/validation |
| --- | --- |
| DatasetMeta | dataset, version, as_of_date |
| Employee | employee_id, full_name, department, role, grade, nullable manager_id, hire_date, tenure_months, work_format, preferred_language, nullable career_goal, skills, last_review_date |
| CareerGoal | target_role, target_grade |
| Skill | skill_id, name, type, category, description |
| RoleProfile | role, grade, required_skills, critical_skills |
| Event | event_id, title, description, type, format, duration_hours, mandatory, target_roles, target_grades, develops_skills, prerequisites, upcoming_sessions |
| SkillGain | skill_id, gain, max_level |
| ActivityHistory | record_id, employee_id, event_id, date, nullable due_date, status, completion_pct, nullable score, nullable feedback_rating, assigned_by |
| EmployeesDataset / EventsDataset / SkillsDataset | meta plus the real named arrays; SkillsDataset also includes proficiency_scale and role_profiles |

Use date types, the documented enums, nonempty IDs, nonnegative tenure/gain, levels 0–5, completion/score 0–100 and rating 1–5. Convert blank optional CSV cells to null in the CSV adapter before model validation. Reject unknown source fields with useful locations rather than silently discarding a changed schema. Do not infer undocumented ID regexes, fixed employee counts or tenure restrictions. Reject duplicate IDs and unknown referenced skills, events, employees, roles/grades or career targets. Validate critical_skills against required_skills and consistent metadata across source envelopes.

Derived API models are distinct: EmployeeSummary, EmployeeDetail (source profile, current_skills, effective participation history), SkillGap, Trajectory, EligibilityResult, CompletionCommand/Result, ImportResult and HRDashboard. Typed dictionaries containing skill levels must not be mutated in place across requests.

Repository interfaces are small, concrete and injectable:

| Repository | Interface and responsibility |
| --- | --- |
| EmployeeRepository | load document; list(); get(employee_id) -> Employee or None |
| EventRepository | load document; list(); get(event_id) -> Event or None |
| SkillRepository | load document; list(); get(skill_id); role_profile(role, grade) |
| HistoryRepository | decode CSV; list(); for_employee(employee_id); get(record_id) |
| DatasetRepository | load raw bundle; decode uploaded bytes through the same adapters; compose indexed DatasetSnapshot from validated source and overlay |
| StateRepository | load state; atomically persist a complete replacement state; no business decisions |

The application dataset service owns the current snapshot, the mutation lock and validation orchestration. Domain repositories expose data from the captured snapshot, not independently reloaded versions. Reads capture one snapshot reference per request. State is never mutated after publication; publish a new snapshot after successful persistence. No background polling or reload daemon is needed.

## 5. Immutable source and mutable state

Raw JSON/CSV is the assessment/history baseline. An ignored state.json contains a schema_version, a fingerprint of the four original data files, a monotonic revision, imported employees/history, runtime completion entries, and idempotency receipts. It never stores a second authoritative mutable skill balance: current skills are derived from assessment plus applicable completions.

Imported rows retain the source schema. Runtime completion entries are application records, not invented starter-kit fields: command_id, employee_id, event_id, nullable source_record_id, participation_date, completed_on. A completion of an existing in_progress or overdue record is an explicit overlay transition, leaving its source row untouched. New participations have no source_record_id. API history views expose effective status and runtime completed_on while preserving the original source details.

Load raw data and state on startup, validate the prospective merged dataset, then publish it. A missing state file means empty state; corrupt state or a mismatched raw fingerprint fails startup with an actionable error. Never silently reset state. Health is ready only after successful loading. Restarts replay derived progress, not mutation commands.

## 6. Deterministic service responsibilities

### Skill projection and progress

Start from Employee.skills, with missing skills equal to zero. Historical completed rows strictly after last_review_date and no later than the effective date contribute gains; older or same-day rows are already represented by the assessment. Historical CSV has no completion timestamp, so its date is the documented approximation for completed rows. Runtime entries instead use completed_on. Order applicable completions by effective completion date and stable record/command ID. For a transitioned source row, count the runtime completion once, never the original row again.

For each skill gain:

```text
new_level = max(current_level, min(current_level + gain, max_level))
```

The outer max prevents a lower-cap course from reducing an existing skill. Validate all levels against 0–5. Only completed participation contributes. Assessments and history are never rewritten to match calculated progress.

### Gaps and trajectory

For each required skill: gap = max(required_level - current_level, 0), with skill_id, name, current_level, required_level and is_critical. The immediate next grade follows Junior -> Middle -> Senior -> Lead in the current role. Lead has next_grade=null, an explicit terminal status and no fabricated promotion requirements. An explicit career_goal is analyzed separately against its target role/grade; it does not replace the immediate-next-grade definition.

Trajectory returns both targets where applicable, gaps, completed activities and available candidate summaries. A target's requirement coverage is sum(min(current, required))/sum(required), with coverage 1 for an empty set and null for an absent target. This is a descriptive metric, not an automatic promotion decision. Completing an event never changes Employee.grade.

### Eligibility

Recommendation candidates must be voluntary, match target_roles and target_grades, satisfy prerequisites using projected skills, and have positive possible gain toward a target requirement. Self-paced events are available immediately. Scheduled events require a session on/after the effective date; retain the next available session in candidate features. Previously completed non-recurring events are excluded. EV_036 is repeatable under the starter-kit's explicit policy; isolate that policy in configuration, rather than scattered event-ID checks.

Return structured rejection reasons as well as eligible candidates. History no-shows, declines and dropped activities are later ranking factors, not invented permanent eligibility bans. There is no lowest-skill recommender in this milestone.

### Completion

Only the employee may complete their own activity. A command includes command_id (UUID), optional source_record_id and optional session_date. For an existing record, verify ownership/event, require in_progress or overdue, and use its participation date. For a new scheduled participation, require session_date from upcoming_sessions and no later than the effective date; for a new self-paced participation, use the effective date. Never accept future completion or arbitrary backdating. New voluntary participations enforce audience/prerequisites; existing assignments can be finished without rechecking historical entry prerequisites. Mandatory events may be completed but are never recommendation targets and earn only the gains explicitly provided by the dataset.

Apply the completion at the effective date, validate prospective state, persist, then return projected changes and trajectory. Reject a new completion of a non-recurring event already completed, even under a new command ID. Recurring participation is unique by employee/event/session date. Completing an existing record twice under different command IDs is a conflict.

Same command ID plus the same normalized principal/resource/body returns the stored original result without a revision change; a changed request with the same key is 409. The receipt and completion are persisted together. This also makes retry after a committed write but lost HTTP response safe.

The default clock is meta.as_of_date = 2026-10-01, not the host clock. An optional application-date configuration override may move forward for demo sessions, never before the dataset snapshot. Existing in-progress and self-paced activities support immediate completion demonstrations. This avoids presenting a future scheduled session as already attended.

### HR aggregates

Return counts of employees below each immediate-next-grade skill requirement and participation status counts by event, using effective history. Also return employees with no eligible candidate, clearly labeled as candidate coverage. Since ranking is deferred, recommendation_status is not_implemented and employees_without_recommendation is null: absence of a computed recommendation is not equivalent to having no candidate. The final AI phase fills the required recommendation-coverage metric. No employee leaderboard or invented dropout-risk score.

## 7. Authorization boundary

Use an Authorization: Bearer token resolved by core/auth.py into Principal(role, employee_id). A server-only DEV_IDENTITIES_JSON setting maps development tokens to identities. Tokens never encode a caller-selected role; do not trust X-Role or X-Employee-ID. Unknown/missing credentials return 401. Only employee and hr are valid roles; employee principals require an existing employee ID. Tests and configuration can assign any valid dataset identity, without business logic tied to the sample user.

Compose may provide explicitly public demo credentials for one employee and HR so the local app starts with one command. These are development fixtures, not real secrets or a production authentication mechanism. The UI lets the tester enter a token and holds it only in memory. The backend's permission checks still apply to every API request. Bind published ports to localhost. README must state that demo tokens are publicly known and unsuitable for deployment; replacing identity verification is required before exposure to untrusted users.

| Action | Employee | HR |
| --- | --- | --- |
| List employees | Own summary only | All summaries |
| Read profile/trajectory | Own only | Any employee |
| Request recommendations | Own only | Any employee for inspection |
| Complete an activity | Own only | Denied in this milestone |
| HR dashboard | Denied | Allowed |
| Dataset import | Denied | Allowed |

FastAPI dependencies enforce require_hr and require_employee_access before returning data; mutation services receive the principal and enforce their command policy too. Wrong role/foreign employee is 403; an authorized lookup of an unknown ID is 404. Authorization happens before exposing resource details. Error bodies and logs must not contain tokens or full uploaded data. Authentication can later replace token lookup while preserving the Principal and authorization dependencies.

## 8. Import contract and atomicity

POST /api/dataset/import accepts multipart employees (optional employees.json with its original meta/employees envelope) and history (optional activity_history.csv with original headers). At least one is required. The jury requirement is additional profiles/history: catalog replacement/import is intentionally outside this milestone. Imported profiles may reference one another or existing managers. Metadata must match the source dataset/version/snapshot; there is no silent clock or schema migration.

Set a 10 MiB total application upload limit, enforced while reading; return 413 if exceeded. Decode bytes as UTF-8 with optional BOM. Do not extract ZIP uploads, follow supplied paths or persist user filenames.

Transaction sequence:

1. Authenticate HR and decode all uploads into typed models. Reject duplicate IDs within an upload, even identical duplicates, with row/field locations.
2. Acquire the same in-process lock used by completion commands; merge against the latest snapshot.
3. Existing employee/record ID with identical normalized source content is an unchanged no-op. Existing ID with different content is 409; no replacement semantics. Compare against immutable imported/source records, not their projected runtime views.
4. Validate the complete prospective dataset and overlay: reference integrity, role/grade/goal requirements, skill ranges, dates/status semantics, and unique participation key (employee_id, event_id, date). A second record ID for the same participation is rejected. Reject duplicate completed non-recurring events and completions that collide with runtime participation/transition records. Preserve a legitimate completed history item before last_review_date, but do not replay its gain.
5. Reject the entire request if anything fails, including a valid employee bundled with invalid history. Do not alter file, revision or active snapshot. Return 422 for invalid schema/references/semantics; 409 for collisions.
6. Build the next state and snapshot. Persist one complete JSON file through a sibling temporary file, flush/fsync and atomic replace on the same filesystem; publish the prepared snapshot only after persistence succeeds. Increment revision only for a mutation. All-no-op import returns unchanged revision.

StateRepository owns file operations; the service owns validation and the lock. Synchronous transaction work must finish before releasing that lock, including during request cancellation. Readers see an entire old or new snapshot. Persistence failure returns 503 and leaves the prior snapshot usable. A process crash after atomic replacement is recovered by startup loading the committed state. This is local single-process durability, not a claim of distributed transactions or protection against every hardware failure.

## 9. API contracts

All /api routes require a bearer token. JSON errors use {error: {code, message, details}}; adapt request-validation errors to that envelope. details contains field/row locations where useful, not sensitive values. Responses that depend on data include revision and as_of_date. Add Cache-Control: no-store to private API responses.

| Method/path | Successful contract |
| --- | --- |
| GET /health | 200 {status: "ok"}; unauthenticated; no employee/config details |
| GET /api/employees | 200 {items: EmployeeSummary[], revision, as_of_date}; visibility-filtered |
| GET /api/employees/{id} | 200 EmployeeDetail: profile, current_skills, history, revision, as_of_date |
| GET /api/employees/{id}/trajectory | 200 Trajectory: employee_id, next_grade, next_grade_gaps, career_goal_analysis, requirement_coverage, completed_activities, candidates, revision, as_of_date |
| POST /api/employees/{id}/recommendations | No body; after authorization/existence check, 501 with code recommendations_not_implemented |
| POST /api/employees/{id}/activities/{event_id}/complete | CompletionCommand body; 200 CompletionResult with command_id, employee_id, event_id, skill_changes, trajectory, revision, as_of_date; exact receipt on retry |
| GET /api/hr/dashboard | 200 HRDashboard with skill_gap_counts, participation_by_event, employees_without_candidate, recommendation_status, employees_without_recommendation, revision, as_of_date |
| POST /api/dataset/import | Multipart inputs above; 200 ImportResult with added/unchanged employee/history counts and revision/as_of_date |

No arbitrary filesystem-path parameter and no raw data download endpoint. Use standard 401/403/404/409/413/422/501/503 meanings described above. API schemas are exposed by FastAPI OpenAPI. Do not return success-shaped fake recommendations.

## 10. Recommendation and AI boundaries

```text
Employee/current skills -> Skill gaps -> History features -> Eligible candidates
    -> Deterministic feature bundle -> Future scoring -> Future LLM refinement
    -> Validated 1–3 recommendations with evidence-backed explanations
```

recommendation_engine.py defines a typed service boundary and the unavailable implementation. Eligibility and feature DTOs prepare future work; no ranking algorithm, model call or synthetic explanation is implemented here.

- RecommendationFactor: kind, observed value(s), provenance references (skill/event/history IDs). Kinds cover current/target grade, required/current skill levels, criticality, attainable gain, completed events, no-shows/declines/drops, duration/format and availability. No arbitrary numerical weights yet.
- RecommendationCandidate: event_id, possible_skill_gains, eligibility, factors. An optional score is null until a scoring implementation exists.
- RecommendationResult: employee_id, recommendations, revision and as_of_date. A successful future result validates 1–3 unique eligible event IDs, explanations and at least three evidence factors. A future no-candidate outcome is a distinct status, not a fake successful recommendation.

ai/client.py defines the provider protocol; ai/recommender.py defines typed refinement input/output and a disabled implementation. The AI receives candidate facts, not filesystem access, secrets, arbitrary employee lists or write authority. Returned activity IDs must be from the eligible input set. Services remain authoritative for all numbers and state changes. OPENAI_API_KEY, NVIDIA_API_KEY and AI_PROVIDER are reserved server-only settings; no SDK or network request is required at startup. Provider connection, prompt design, timeout/fallback and recommendation-quality evaluation belong to the next milestone. Respect the specification's data-use restrictions before any future external transmission.

## 11. Frontend boundaries

Use Next.js App Router, TypeScript and Tailwind. Avoid introducing shadcn/ui solely for this small skeleton. Layout supplies navigation; page components compose small domain components. Private data is fetched client-side after a development token is entered, avoiding server-side user-data caching and eliminating a second proxy/backend layer.

- `/`: development-token entry, visible employee summaries and navigation. The backend determines the returned employee set. No public employee directory.
- `/employee/[id]`: profile, current skills, target/gaps, history and deterministic available activities; minimal completion control with one command UUID per user attempt, retained for retries. Explain that recommendations are not yet implemented. Handle unauthorized, missing, loading and error states.
- `/hr`: basic skill gaps, participation and candidate coverage plus an employees/history file import form. Mark recommendation coverage unavailable. Backend rejects employee access even if the page is opened directly.

lib/api.ts is the sole fetch layer: use NEXT_PUBLIC_API_URL, attach the current token, handle structured errors, and serialize commands/uploads. Components do not contain backend URLs. lib/types.ts mirrors public API DTOs, not internal repositories/state. Session provider clears cached displayed data when the token changes and discards responses from the previous identity. Tokens are not stored in browser localStorage or bundled environment variables.

Keep accessible labels, keyboard-operable forms, ordinary semantic tables and clear empty/error states. No dashboard chart library, gamification, optimistic skill gains or frontend authorization claims. After mutation, refetch affected data from the API.

## 12. Docker and configuration

Two services only: frontend on localhost:3000 and backend on localhost:8000. Backend runs one Uvicorn worker, mounts data/raw read-only and a named volume at its configured state directory. Frontend uses a multi-stage Next.js build and runtime image. NEXT_PUBLIC_API_URL is supplied as a frontend build argument (default http://localhost:8000) because browser requests target the host, not Docker's internal service name. Backend healthcheck gates dependent service startup; normal frontend errors still handle later outages.

Root docker-compose.yml supplies local demo defaults, so docker compose up --build works after the starter kit is placed in data/raw. An example environment documents API URL, raw/state directories, allowed frontend origin, DEV_IDENTITIES_JSON, optional application date, and reserved AI settings. Use no secret-valued NEXT_PUBLIC variables. Ignore real .env files, mutable state, node_modules, build outputs, Python caches and local virtual environments. Pin actual compatible dependency versions and lock frontend dependencies during implementation; version selection is not inferred from this design date.

Minimum runtime dependencies: FastAPI, Pydantic, Uvicorn and python-multipart; Python standard library for storage/configuration. Tests add pytest and httpx. No extra configuration library is necessary. The README must distinguish enforcement of authorization from the deliberately limited development identity mechanism and explain the one-worker constraint and state reset procedure.

## 13. Testing and verification

Use Superpowers test-driven development for deterministic behavior and state/API rules in the later implementation stage. Tests must not mutate the real raw dataset.

| Area | Required evidence |
| --- | --- |
| Source fidelity/loading | Copy hashes equal archive hashes; actual 200/40/60/32/2743 dataset parses; source fields/envelopes and nullable CSV values preserved; invalid references/duplicates rejected |
| Projection | Before/on/after assessment boundary; chronological replay; only completed status; missing skill=0; cap enforcement; no regression; no duplicate application after restart |
| Gaps/trajectory | Role-specific requirements, critical flags, zero-clamped gaps, Lead, cross-role career goal, coverage calculation |
| Eligibility | Mandatory exclusion, audience, prerequisites, session clock, self-paced availability, completed-event exclusion and recurring exception |
| Completion | Ownership, event/record mismatch, status transition, future-date rejection, regular/recurring uniqueness, exact retry, conflicting key, persistence failure and restart |
| Import | Fresh unknown IDs; references across uploaded/existing data; exact retry; conflicting IDs; semantic duplicates; whole-request rejection; collision with runtime state; size limit; no raw changes |
| Concurrency | Concurrent import/completion serialize against latest revision; simultaneous retries apply once; failed writes do not publish memory-only changes |
| Authorization/API | 401, cross-employee 403, HR restriction, authorized 404, visibility-filtered list, protected imports, explicit recommendation 501, redacted error shape |
| HR | Gap and participation counts reflect imports/completions; unavailable recommendations not confused with zero eligible candidates |
| Frontend/deployment | Typecheck and production build; browser smoke through both roles, import, completion and error states; Compose config and real startup/health smoke |

Use small in-memory model fixtures and temporary directories for failure/edge tests plus real-data read-only loading tests. Capture raw hashes before and after the suite. Verify backend import and a live /health request, not only TestClient. Run Docker startup when the host supports it; report unavailable infrastructure as an unverified check, never a pass. Inspect Git changes for credentials and ensure README commands match implementation.

UI response target is two seconds on the supplied dataset; record a local smoke measurement without claiming production guarantees. The ten-second AI requirement remains a later acceptance criterion because AI is deferred.

## 14. Implementation phases and review handoff

These phases describe scope and dependency order; the executable Superpowers implementation plan is written only after approval of this spec.

1. Preserve raw starter-kit bytes; create source schemas, file adapters, snapshot validation and read-only loading tests.
2. Implement and test projection, gaps, trajectory and deterministic eligibility as small functions/services.
3. Add development principal lookup, authorization dependencies, durable state, completion/import transactions and their failure/retry tests.
4. Wire FastAPI endpoints, basic HR aggregates and explicit recommendation unavailability; verify public contracts and access rules.
5. Build the minimal Next.js pages and typed API client, then Docker/configuration and operating documentation.
6. Run the complete verification set, perform code review, fix material findings and write docs/handoff.md with actual files, commands, results, limitations and next work.

Suggested collaboration boundaries after approval: schemas/repositories and state transactions stay under one owner while their interfaces stabilize; deterministic services and frontend consume those contracts. Do not dispatch implementation agents before the plan's execution-method review.

Next product milestone: multi-factor scoring and AI refinement with evidence-backed explanations, followed by recommendation coverage on the HR screen and evaluation against unfamiliar jury-style profiles. Preserve deterministic calculations and authorization throughout.

## 15. Spec self-review

- Source compatibility: real source names, envelopes, clock, assessment semantics and recurring-event rule are reflected; runtime-only fields remain separate.
- Scope: two services and local files; no additional infrastructure or full recommendation implementation.
- Consistency: imports and completions share one transaction boundary; persistent receipts and derived skills prevent duplicate gains; HR recommendation metrics explicitly acknowledge the deferred engine.
- Ambiguity resolved: explicit append/no-op/conflict import semantics, employee-only completion, development identity mapping, source-record transitions, next-grade versus career-goal behavior, date policy and one-worker persistence limits.
- Approval boundary: this document is proposed. No product code, dependency installation or execution plan was created in this design phase.
