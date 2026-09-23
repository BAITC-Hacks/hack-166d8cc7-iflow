# Career Quest foundation handoff

Subsequent context implementation: the full linked recommendation payload, prompts,
JSON adapter and authorized context route are now implemented. The default external
provider remains disabled. Current behavior and integration details are documented
in [llm-context.md](llm-context.md); the foundation verification record below describes
the earlier implementation and is preserved as historical evidence.

Verified 2026-09-23 on branch `codex/career-quest-foundation`, based on `main` at `59399d0`. Product implementation is in the managed worktree:
`C:/Users/zhasy/.codex/worktrees/career-quest-foundation/hack-166d8cc7-iflow`.
The original checkout has not been merged. All 14 implementation tasks have deliverables; the explicit browser race-test limitation is recorded below.

## What is ready

The real starter kit loads through Pydantic/repositories: **200 employees, 40 events, 60 skills, 32 role/grade profiles, 2,743 history records**, snapshot date **2026-10-01**. All seven extracted raw files match their SHA-256 manifest. JSON/CSV sources are immutable and mounted read-only in Docker.

Employees have a profile, deterministic current skills, next-grade and career-goal gaps, trajectory, eligible activities and completion. HR can inspect employees, view gap/participation aggregates and import same-schema jury profiles/history. Backend dependencies/services enforce employee/HR boundaries. Development identities are public demo credentials, not production authentication.

Recommendations deliberately return **501**. Candidate evidence and future AI validation interfaces are ready; there is no scoring, provider call or invented recommendation.

## Architecture decisions

- Next.js/TypeScript/Tailwind and FastAPI/Pydantic remain separate. Components use `frontend/src/lib/api.ts`.
- Services calculate projection, gaps, eligibility, trajectory and gains. File access stays in repositories.
- Assessment skills are the baseline; completed history strictly after the review date contributes gains. No gain reduces an already higher skill.
- One mutable JSON overlay contains imported records, runtime completions and persisted command receipts. One process/worker and one mutation lock; validate, write temporary file, flush/fsync, atomically replace, then publish the snapshot.
- Imports validate the whole prospective dataset. Identical records are no-ops; conflicting IDs/participations reject without mutation. Completion retries reuse UUID/request and return their original persisted receipt.
- AI lives behind `backend/app/ai`. No infrastructure beyond two application containers and a local named volume.
- Small additions to the requested tree (dataset/state/response models, eligibility/completion services, validation errors, auth dependencies) keep actual responsibilities explicit. Empty hooks/prompt scaffolds and shadcn initialization were unnecessary for this minimal UI.

## Run

From this worktree:

```powershell
docker compose up --build -d
docker compose ps
```

Open http://localhost:3000; backend health is http://localhost:8000/health.
Use `demo-employee` for E0001, `demo-active` for E0004, or `demo-hr` for HR. Tokens are entered into the Development token field and held only in memory. Reloading clears identity.

See [README](../README.md) for native Python/npm setup, environment variables, endpoint contracts, import format and intentional state reset. Normal restart preserves the named volume. No API keys are required.

```powershell
# From root after installing backend/requirements-dev.txt into .venv:
.venv/Scripts/python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
docker compose config --quiet
```

## Verification evidence

| Check | Actual result |
| --- | --- |
| Backend module import and startup | Passed; container healthy; GET /health returns status ok |
| Backend full suite | **135 passed**, no skipped tests; one upstream Starlette/httpx deprecation warning |
| Source parsing and hashes | Real counts above; all seven raw hashes match |
| Frontend clean dependency installation | npm ci passed, including clean Docker build stage |
| TypeScript and production build | Passed; /, /employee/[id], /hr build |
| Compose validation/build/start | Passed; backend and frontend running |
| Browser employee slice | Real profiles, current skills, targets, gaps and candidates rendered; foreign employee denied |
| Browser mutation | E0004 self-paced statistics completion displayed 2 -> 3, refreshed trajectory |
| Browser HR import | JURY_DEMO profile and JURY_HISTORY imported; HR revision changed once |
| Unfamiliar employee identity | Temporary demo-jury configuration accessed only JURY_DEMO; profile/gaps/candidates rendered |
| Completion and retry | JURY_HISTORY transitioned; Python 1 -> 2; same command returns exactly identical receipt |
| Container restart | Imported employee and receipt survived; retry still Python 2 |
| Late-invalid import | ROLLBACK_DEMO plus unknown-event history rejected; employee absent; revision unchanged |
| Reimport after completion | Original imported in-progress source row is a no-op; runtime transition retained |
| Negative authorization | Foreign read, employee import and HR completion denied; recommendations explicit 501 |
| HR aggregates | Reflected revision and completion |
| Representative live read | Synthetic trajectory **10 ms** over local IPv4; earlier real E0001 read 105 ms; no production latency claim |
| Review fixes | Five new regression cases observed RED then GREEN; final full suite 135/135 |
| Browser error feedback | Invalid CSV displays activity_history.csv / 2 / completion_pct; no uploaded values echoed |
| Git hygiene | diff --check passed; no tracked .env/runtime state/build caches; credential-pattern scan found no keys |

A restart smoke initially connected before Uvicorn was ready; it was rerun after Docker reported healthy and passed. This was not suppressed as a passing attempt.

**Not verified:** the exact controlled slow-network identity-switch scenario for an in-flight read/mutation could not be exercised with the available browser control surface. Normal identity switching and foreign-profile denial were verified; independent review confirmed keyed private-tree remounting, request cancellation and stale mutation guards. This remains a focused browser test for the next agent, not a claimed automated pass.

## Final independent review

One fresh reviewer found two Important issues and no Critical/Minor findings:
1. Early import authorization/size rejections bypassed CORS. Fixed middleware order; 401/403/413 allowed-origin regression tests pass.
2. Import errors lacked usable row/field feedback. CSV/schema and semantic errors now carry sanitized locations; HR renders them. Schema and cross-reference rollback tests pass, and visible browser feedback was checked.

No second review was dispatched, following Native workflow's one reviewed fix pass.

## Rulings made during execution

1. Added backend pytest path configuration so root test commands work, and Git `-text` attributes to preserve source bytes. Actual execution base was 59399d0, not the older design commit. Cost if wrong: test invocation/attribute adjustment; hash checks guard raw bytes.
2. Starter-kit README says non-recurring events cannot repeat, but real source history repeats annual mandatory compliance EV_001–003. Preserve source history and allow distinct existing mandatory compliance assignments to complete; imported distinct zero-gain compliance history is accepted. Voluntary non-recurring events remain unique, except documented EV_036. Cost if wrong: permissive completion of already assigned zero-gain compliance.

Deferred minors: none reported.

## Limits and next task

Single-process local MVP, replaceable demo identity mechanism, assessment-date replay approximation and fixed dataset clock. Advancing APPLICATION_DATE requires deliberate demo configuration; do not move it backward after recording newer completions. State reset is explicit and destructive only to the chosen disposable overlay. Catalog replacement is outside this import contract. HR recommendation coverage remains null.

The running Docker volume includes the synthetic JURY_DEMO profile, JURY_HISTORY and its completion from verification; source files are unchanged. Temporary demo-jury identity was used for verification, then default Compose identities restored. HR can still inspect the synthetic record. Test fixture files/runtime state were never committed.

**Next product task: multi-factor recommendation scoring and LLM refinement**, before frontend polish:
1. Capture current snapshot revision/date, next-grade and separately labeled career-goal analysis.
2. Consume candidates from [eligibility.py](../backend/app/services/eligibility.py) and [recommendation_engine.py](../backend/app/services/recommendation_engine.py).
3. Preserve [RecommendationFactor / Candidate / Result](../backend/app/schemas/recommendation.py): current and target grades, skill current/required levels, critical relevance, attainable gain, past completions, no-show/decline/drop evidence, availability and source IDs.
4. Add deterministic multi-factor scoring; then send only allowed candidates/facts through [AI client interface](../backend/app/ai/client.py).
5. Use [AI result validation](../backend/app/ai/recommender.py) to enforce 1–3 distinct eligible events, supported evidence and matching employee/revision/date. Deterministic logic remains authoritative for skills, gains, events and progress.
6. Replace 501, populate HR recommendation coverage and verify unfamiliar scenarios plus the ten-second recommendation budget. Add the controlled frontend identity race test noted above.

## Final tracked file tree

The following tree lists the committed application/data/documentation boundary (generated caches and runtime state excluded).

```text
.env.example
.gitattributes
.gitignore
README.md
backend/
  .dockerignore
  Dockerfile
  app/
    __init__.py
    ai/
      __init__.py
      client.py
      recommender.py
    api/
      __init__.py
      activities.py
      dataset.py
      dependencies.py
      employees.py
      hr.py
      recommendations.py
    core/
      __init__.py
      auth.py
      config.py
      errors.py
    main.py
    repositories/
      __init__.py
      dataset.py
      employees.py
      events.py
      history.py
      skills.py
      state.py
      validation.py
    schemas/
      __init__.py
      activity.py
      common.py
      dataset.py
      employee.py
      history.py
      recommendation.py
      responses.py
      skill.py
      state.py
    services/
      __init__.py
      completion.py
      dataset.py
      eligibility.py
      hr.py
      progress_engine.py
      recommendation_engine.py
      skill_gap.py
      trajectory.py
  pytest.ini
  requirements-dev.txt
  requirements.txt
  tests/
    conftest.py
    test_api.py
    test_completion.py
    test_data_loading.py
    test_eligibility.py
    test_hr.py
    test_import.py
    test_progress.py
    test_recommendation_boundary.py
    test_skill_gap.py
    test_state.py
data/
  fixtures/
    README.md
    raw-sha256.json
  raw/
    README.kz.md
    README.md
    README.ru.md
    activity_history.csv
    employees.json
    events.json
    skills.json
docker-compose.yml
docs/
  architecture.md
  data-model.md
  discovery.md
  handoff.md
  superpowers/
    plans/
      2026-09-23-career-quest-foundation.md
    specs/
      2026-09-23-career-quest-design.md
frontend/
  .dockerignore
  Dockerfile
  next-env.d.ts
  next.config.ts
  package-lock.json
  package.json
  postcss.config.mjs
  src/
    app/
      employee/
        [id]/
          page.tsx
      globals.css
      hr/
        page.tsx
      layout.tsx
      page.tsx
    components/
      employee/
        profile.tsx
        trajectory.tsx
      hr/
        dashboard.tsx
      session-provider.tsx
      ui/
        status-message.tsx
    lib/
      api.ts
      types.ts
  tsconfig.json
```
