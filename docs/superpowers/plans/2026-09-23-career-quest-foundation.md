# Career Quest Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a verified, file-backed Career Quest foundation with real-data employee trajectories, backend authorization, completion/import workflows and a minimal frontend, ready for the next recommendation milestone.

**Architecture:** Next.js calls FastAPI through one typed client. Pure domain functions consume validated repository snapshots; one backend process serializes mutations into one atomic JSON overlay while preserving raw data. Recommendation evidence is deterministic and AI remains disabled behind a replaceable interface.

**Tech Stack:** Next.js App Router, TypeScript, Tailwind; Python, FastAPI, Pydantic, Uvicorn, python-multipart; pytest/httpx; Docker Compose.

**Spec:** [Approved architecture](../specs/2026-09-23-career-quest-design.md). Read alongside [discovery](../../discovery.md). The user approved the spec for planning on 2026-09-23; its original proposed-status header is historical. This implementation plan is awaiting approval and an execution-method choice.

## Global Constraints

- “Use the existing repository root, with separate frontend and backend projects.”
- “Raw starter-kit files are copied byte-for-byte from the archive, excluding macOS metadata.”
- “Services do not open files or depend on HTTP exceptions.”
- “The file approach requires exactly one backend process/worker and serialized mutations; these limits are explicit.”
- “No ranking algorithm, model call or synthetic explanation is implemented here.”
- “Only the employee may complete their own activity.”
- “Reject unknown source fields with useful locations rather than silently discarding a changed schema.”
- “The default clock is meta.as_of_date = 2026-10-01, not the host clock.”
- “Set a 10 MiB total application upload limit, enforced while reading; return 413 if exceeded.”
- “Tokens are not stored in browser localStorage or bundled environment variables.”
- “Use no secret-valued NEXT_PUBLIC variables.”
- “No public upload of the dataset is part of this work; the specification restricts it to the hackathon.”
- Preserve original names/envelopes and all source fields. No extra infrastructure, public employee rankings, rewards, auth platform, frontend polish or real AI provider SDK.
- User planning guidance: preserve correctness with one state file, one lock and one atomic replacement helper. No journal, background writer, transaction framework, backup subsystem or distributed locking.
- Stop at this plan. Do not install packages, scaffold projects, invoke execution skills or spawn implementation workers until the user approves and selects execution method.

## Review Focus

Five easily missed conditions, with explicit ownership below:

1. Current skill exceeds an activity cap: completing it must not reduce the skill (Task 2).
2. A retry arrives after a write succeeded but its HTTP response was lost: return the persisted receipt without another gain, including after restart (Task 8).
3. A known history row is reimported after runtime completion: compare immutable source content, retain the runtime transition and apply no second gain (Task 9).
4. The development token changes while a profile request is in flight: neither old data nor a delayed old response may appear under the new identity (Task 6).
5. An HR upload fails near its end: reject the entire import and preserve both state revision and the raw file hashes (Tasks 9–10).

---

## File ownership and interfaces before tasks

Paths below are repository-relative; all shell commands explicitly identify their working directory. The tree in the approved spec remains the target. These additional test files separate meaningful concerns: backend/tests/test_state.py, test_completion.py, test_recommendation_boundary.py and test_hr.py. No additional runtime service is introduced.

| Files | Responsibility / owner |
| --- | --- |
| backend/app/schemas/{employee,skill,activity,history,dataset}.py | Source models, enums, envelopes; Task 1 |
| backend/app/repositories/{employees,events,skills,history,dataset}.py | JSON/CSV decoding and indexed, read-only repository views; Task 1 |
| backend/app/services/progress_engine.py | Completion projection and gain arithmetic; Task 2 |
| backend/app/services/{skill_gap,trajectory}.py | Target resolution, gaps, coverage and trajectory; Task 3 |
| backend/app/services/eligibility.py | Eligibility plus factual candidate evidence; Task 4 |
| backend/app/schemas/{responses,recommendation}.py | Public DTOs and evidence contracts; Tasks 2–4, extended by each owning feature |
| backend/app/core/{config,auth,errors}.py | Environment parsing, replaceable identities, domain errors; Task 5 |
| backend/app/main.py, api/{dependencies,employees}.py | Composition/lifespan and read endpoints; Task 5 |
| backend/app/services/dataset.py | Snapshot holder initially; one mutation coordinator after Task 7 |
| backend/app/schemas/state.py, repositories/state.py | Overlay/receipt schema and atomic file IO; Task 7 |
| backend/app/services/completion.py, api/activities.py | Completion policy and HTTP adapter; Task 8 |
| backend/app/api/dataset.py | Bounded import upload adapter; Task 9 |
| backend/app/services/recommendation_engine.py, ai/{client,recommender}.py, api/recommendations.py | Disabled recommendation boundary and future-result validation; Task 10 |
| backend/app/services/hr.py, api/hr.py | Honest deterministic HR aggregates; Task 11 |
| frontend/src/lib/{api,types}.ts | Single API client and matching public DTOs; Tasks 6 and 12 |
| frontend/src/components/session-provider.tsx | In-memory demo credentials and identity-change isolation; Task 6 |
| frontend/src/app/{layout.tsx,globals.css,page.tsx,employee/[id]/page.tsx} | Minimal read-only vertical slice; Task 6 |
| frontend/src/components/{employee/profile.tsx,employee/trajectory.tsx,ui/status-message.tsx} | Small display components; Task 6 |
| frontend/src/app/hr/page.tsx, components/hr/dashboard.tsx | HR aggregates and import form; Task 12 |
| Dockerfiles, Compose, .env.example, README.md, docs/{architecture,data-model}.md | Reproducibility and accurate operating instructions; Task 13 |
| docs/handoff.md | Actual results, limitations and immediate recommendation handoff; Task 14 |

Create Python __init__.py files when their package first appears. No empty future hooks, prompt files or unused UI components. Use Pydantic DTOs for source/API data and an ordinary frozen dataclass for DatasetSnapshot; repository internals can be simple indexed dictionaries exposed read-only. Do not mutate a published snapshot.

### Shared contract vocabulary

Define these in the named tasks; do not invent alternate names in downstream implementations:

- Task 1: SourceBundle(meta, employees, events, skills, role_profiles, proficiency_scale, history); DatasetRepository(raw_dir: Path).load() -> SourceBundle; parse_employees(data: bytes) -> EmployeesDataset; parse_history(data: bytes) -> tuple[ActivityHistory, ...]; build_snapshot(bundle: SourceBundle, revision: int = 0) -> DatasetSnapshot. Snapshot exposes meta, revision, and employees/events/skills/history repository views.
- Task 1 repository views: employees.list()/get(id), events.list()/get(id), skills.list()/get(id)/role_profile(role, grade), history.list()/get(id)/for_employee(id). get returns None for missing data; callers translate that intentionally. The snapshot also retains its SourceBundle for validated merges.
- Task 2: EffectiveCompletion(completion_key: str, event_id: str, completed_on: date); project_skills(employee: Employee, completions: Sequence[EffectiveCompletion], events: EventRepository, as_of_date: date) -> dict[str, int]; apply_gains(current: Mapping[str, int], gains: Sequence[SkillGain]) -> dict[str, int].
- Task 3: calculate_gaps(current: Mapping[str, int], profile: RoleProfile, skills: SkillRepository) -> list[SkillGap]; build_trajectory(employee_id: str, snapshot: DatasetSnapshot, as_of_date: date) -> Trajectory. Task 7 adds runtime_completions to DatasetSnapshot, defaulting to an empty tuple; Task 8 teaches the history adapter to consume it. The public trajectory signature remains unchanged.
- Task 4: evaluate_event(employee: Employee, current: Mapping[str, int], targets: Sequence[TargetAnalysis], history: Sequence[ParticipationView], event: Event, as_of_date: date, repeatable_event_ids: frozenset[str]) -> RecommendationCandidate. Produce accepted and rejected results; callers filter on eligibility. No score computation.
- Task 5: Principal(role: Literal['employee', 'hr'], employee_id: str | None); Settings.from_env() -> Settings; create_app(settings: Settings) -> FastAPI; DatasetService(snapshot: DatasetSnapshot) stores the current snapshot and exposes read-only capture(). Later tasks extend construction to include the state repository without changing capture().
- Task 7: MutableState(schema_version, raw_fingerprint, revision, imported_employees, imported_history, completions, receipts); StateRepository(path: Path).load(expected_fingerprint: str) -> MutableState; save(state: MutableState) -> None. DatasetService gains lock, state, state_repository and commit(next_state: MutableState) -> DatasetSnapshot, called while holding lock.
- Task 8: complete_activity(principal: Principal, employee_id: str, event_id: str, command: CompletionCommand, dataset: DatasetService, as_of_date: date) -> CompletionResult.
- Task 9: import_dataset(principal: Principal, employees: EmployeesDataset | None, history: tuple[ActivityHistory, ...] | None, dataset: DatasetService) -> ImportResult.
- Task 11: build_hr_dashboard(snapshot: DatasetSnapshot, as_of_date: date) -> HRDashboard. Read runtime_completions from that captured snapshot, never from a separately fetched mutable state revision.

RuntimeCompletion is an overlay schema, never an additional field in employees.json/events.json/skills.json or the CSV. All sources of effective history feed one projection adapter, defined in Task 2 and extended in Task 8.

### Execution conventions

- Run Python test commands from backend/: `python -m pytest tests/<file>.py -q`. Use a local virtual environment. Requirements-dev includes requirements.txt plus pytest/httpx.
- Every logic task: add the named tests first, run and confirm the intended missing/incorrect behavior, implement the smallest passing code, rerun its tests, and commit only that task's explicit paths. An import/setup failure unrelated to the behavior is not sufficient RED evidence.
- Test snippets below are concrete representative tests; the adjoining named cases are mandatory additional cases. Each case specifies its input and assertion. No tests should modify data/raw.
- Use `git add -- <task paths>` and `git commit -m '<task message>'` after GREEN. Do not push or publish data. At execution start, apply the selected workflow's repository/worktree rules; this plan itself creates no worktree.
- Steps are intended to take roughly 2–5 minutes each; tasks combine several such steps. If a step grows, split its listed assertions into separate RED/GREEN iterations rather than introducing new architecture.

## Task 1: Load and validate the actual starter kit

**Create:** backend/requirements.txt, backend/requirements-dev.txt; backend/app/schemas/{employee,skill,activity,history,dataset}.py; backend/app/repositories/{employees,events,skills,history,dataset}.py; backend/tests/conftest.py, backend/tests/test_data_loading.py; data/raw/{employees.json,events.json,skills.json,activity_history.csv,README.md,README.kz.md,README.ru.md}; data/fixtures/README.md; .gitignore. Include package __init__.py files.

**Consumes:** archive `C:/Users/zhasy/Downloads/career_quest_dataset.zip`, only its `case_1/career_quest_dataset/` named files, and the source schema tables in spec §4.

**Produces:** SourceBundle, repository interfaces and build_snapshot defined above. SourceBundle uses tuples of typed records; metadata retains the dataset clock.

- [ ] Copy the seven approved archive members byte-for-byte and record SHA-256 values for the four data files in data/fixtures/README.md. Do not unpack macOS metadata. Select compatible runtime versions from official package metadata at execution time, pin backend packages, and install only the listed dependencies into a local environment. Ignore .env, .venv, state, caches and frontend build/install output; retain .env.example.
- [ ] Create conftest fixtures: real_bundle loads the actual raw files; make_employee clones the first real employee through model_validate after changes with manager_id=None, employee_id='TEST_EMP', grade='Middle', skills={'SK_PYTHON': 1}, last_review_date='2026-09-01'; make_event clones EV_012 through model_validate after changes; make_history uses the exact CSV fields below. tiny_bundle replaces employees/events/history with supplied fixtures while retaining the real skill/role catalogs. events and skills return repository views from build_snapshot(tiny_bundle); clock returns date(2026, 10, 1). api_settings later points raw_dir to a temporary serialized tiny_bundle, not the original files. Keep serializers used to create temporary source files in the test fixture module, never production services.

```python
def history_payload(**changes):
    return {
        'record_id': 'TEST_REC', 'employee_id': 'TEST_EMP',
        'event_id': 'EV_012', 'date': '2026-09-20', 'due_date': None,
        'status': 'completed', 'completion_pct': 100, 'score': None,
        'feedback_rating': None, 'assigned_by': 'self', **changes,
    }

def test_real_dataset_counts(real_bundle):
    assert (len(real_bundle.employees), len(real_bundle.events),
            len(real_bundle.skills), len(real_bundle.role_profiles),
            len(real_bundle.history)) == (200, 40, 60, 32, 2743)
    assert real_bundle.meta.as_of_date.isoformat() == '2026-10-01'
```

- [ ] Run `python -m pytest tests/test_data_loading.py -q` RED. Add named cases: test_employee_roundtrip_preserves_all_fields (first employee equals JSON payload after date serialization); test_csv_blank_fields_are_none (blank due_date/score/rating); test_unknown_fields_rejected; test_duplicate_ids_rejected; test_unknown_skill_employee_event_manager_references_rejected (parameterized); test_invalid_role_grade_and_goal_rejected; test_metadata_mismatch_rejected; test_unknown_employee_returns_none; test_raw_hashes_match_manifest. The fixed counts are test expectations, never application validation rules.
- [ ] Implement source models with `ConfigDict(extra='forbid')`, all documented enums/ranges and envelopes. Normalize CSV blanks, reject duplicate headers/rows by ID, and decode UTF-8 BOM. Validate the entire bundle before indexing. Keep the parser in repositories and business consumers free of file IO.

```python
def parse_history(data: bytes) -> tuple[ActivityHistory, ...]:
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    # Compare headers to ActivityHistory.model_fields before consuming rows.
    rows = ({key: (None if value == '' else value)
             for key, value in row.items()} for row in reader)
    return tuple(ActivityHistory.model_validate(row) for row in rows)
```

- [ ] Run the file GREEN; record real-data loading success and byte hashes. Commit `feat: load validated Career Quest starter data`.

**Checkpoint A:** real data loads without invented fields, mutation or network services.

## Task 2: Project current skills without double counting

**Create:** backend/app/services/progress_engine.py, backend/app/schemas/responses.py, backend/tests/test_progress.py. **Modify:** backend/app/schemas/history.py (derived EffectiveCompletion/ParticipationView, separate from ActivityHistory), backend/tests/conftest.py.

**Consumes:** Employee, SkillGain, EventRepository and ActivityHistory. **Produces:** apply_gains, project_skills, historical_completions(history: Sequence[ActivityHistory]) -> list[EffectiveCompletion], and ParticipationView with source_record_id, event_id, date, status, completed_on and optional source record.

- [ ] Add and run these tests RED, with actual assertions:

```python
def test_gain_does_not_reduce_skill():
    gain = SkillGain(skill_id='SK_PYTHON', gain=1, max_level=3)
    assert apply_gains({'SK_PYTHON': 4}, [gain]) == {'SK_PYTHON': 4}

@pytest.mark.parametrize('day,expected', [('2026-08-31', 1),
    ('2026-09-01', 1), ('2026-09-02', 2), ('2026-10-02', 1)])
def test_assessment_and_snapshot_boundaries(day, expected, make_employee, events):
    c = EffectiveCompletion(completion_key='r1', event_id='EV_012',
                            completed_on=date.fromisoformat(day))
    assert project_skills(make_employee(), [c], events,
                          date(2026, 10, 1))['SK_PYTHON'] == expected
```

- [ ] Add test_missing_skill_starts_at_zero (absent Python +1 ->1); test_gain_is_capped (3 +2 cap4 ->4); test_noncompleted_statuses_do_not_contribute (all five other statuses); test_same_completion_key_applied_once; test_projection_does_not_mutate_employee; test_chronological_projection (two distinct events with different caps produce the expected chronological result); test_unknown_event_rejected (domain failure rather than silently losing gain).
- [ ] Run `python -m pytest tests/test_progress.py -q`, confirm RED, then implement:

```python
levels = dict(employee.skills)
seen = set()
for completion in sorted(completions, key=lambda c: (c.completed_on, c.completion_key)):
    if completion.completion_key in seen:
        continue
    seen.add(completion.completion_key)
    if employee.last_review_date < completion.completed_on <= as_of_date:
        event = events.get(completion.event_id)
        if event is None:
            raise ValueError('Unknown completion event')
        levels = apply_gains(levels, event.develops_skills)
# apply_gains copies its input and uses max(old, min(old + gain, max_level)).
```

- [ ] Rerun GREEN and Task 1 regression. Commit `feat: project deterministic employee skill progress`.

## Task 3: Calculate gaps and both career targets

**Create:** backend/app/services/skill_gap.py, backend/app/services/trajectory.py, backend/tests/test_skill_gap.py. **Modify:** backend/app/schemas/responses.py.

**Consumes:** snapshot, projected skills, RoleProfile. **Produces:** SkillGap(skill_id, name, current_level, required_level, gap, is_critical); TargetAnalysis(role, grade, gaps, requirement_coverage); Trajectory(employee_id, next_grade, next_grade_gaps, career_goal_analysis, requirement_coverage, completed_activities, candidates, revision, as_of_date). candidates is empty until Task 4 joins it.

- [ ] Add and run `python -m pytest tests/test_skill_gap.py -q` RED:

```python
def test_gaps_preserve_criticality(skills):
    target = RoleProfile(role='Backend Engineer', grade='Senior',
        required_skills={'SK_PYTHON': 4}, critical_skills=['SK_PYTHON'])
    result = calculate_gaps({'SK_PYTHON': 2}, target, skills)
    assert (result[0].gap, result[0].is_critical) == (2, True)
```

- [ ] Add test_gap_never_negative (5 vs4 ->0); test_missing_skill_gap (absent vs3 ->3); test_next_grade_order; test_lead_has_no_next_grade (null coverage, no next-grade gaps); test_cross_role_goal_stays_separate (current Backend next-grade target plus Frontend explicit goal); test_coverage_uses_capped_levels (5/4 and1/2 ->5/6); test_empty_requirements_coverage_is_one; test_trajectory_unknown_employee (domain not-found).
- [ ] Implement target lookup and pure arithmetic; collect completed activities from the same history projection used in Task 2. Preserve full requirement entries including zero gaps so downstream evidence can explain levels.

```python
gap = max(required_level - current.get(skill_id, 0), 0)
denominator = sum(profile.required_skills.values())
coverage = (sum(min(current.get(k, 0), v)
                for k, v in profile.required_skills.items()) / denominator
            if denominator else 1.0)
```

- [ ] Run GREEN and loading/projection regression. Commit `feat: expose next-grade and career-goal trajectories`.

## Task 4: Eligible activities and factual recommendation inputs

**Create:** backend/app/services/eligibility.py, backend/app/schemas/recommendation.py, backend/tests/test_eligibility.py. **Modify:** backend/app/services/trajectory.py, backend/app/schemas/responses.py as needed for typed candidate lists, backend/tests/conftest.py for eligible_case.

**Consumes:** evaluate_event signature in shared vocabulary; target gaps and effective participation history. **Produces:** EligibilityResult(eligible, reasons, next_session); RecommendationFactor(kind, values, source_ids); RecommendationCandidate(event_id, title, possible_skill_gains, eligibility, factors, score=None). values contains only scalar facts or scalar lists, never model-generated facts. Targets carry role/grade labels so cross-role facts remain distinguishable.

- [ ] Add tests and run `python -m pytest tests/test_eligibility.py -q` RED:

```python
@pytest.mark.parametrize('mandatory,expected', [(False, True), (True, False)])
def test_mandatory_is_not_a_recommendation_target(mandatory, expected,
        eligible_case):
    args = eligible_case  # fixture: Middle Backend, Python1, target Python4,
                          # EV_012 self-paced, no history, clock 2026-10-01.
    candidate = evaluate_event(**{**args,
        'event': args['event'].model_copy(update={'mandatory': mandatory})})
    assert candidate.eligibility.eligible is expected
```

- [ ] Add test_wrong_role_or_grade (reason codes audience_role/audience_grade); test_unmet_prerequisite; test_zero_attainable_gain; test_self_paced_no_sessions_allowed; test_scheduled_event_requires_current_or_future_session; test_completed_event_excluded; test_repeatable_club_allowed; test_no_shows_are_facts_not_permanent_bans; test_feature_bundle_preserves_all_required_evidence. The last fixture has prior completed, no_show, declined and dropped records: assert all four status counts and record IDs, current grade, each target grade, current/required levels, criticality, capped gain and next-session evidence. Assert score is None.
- [ ] Implement reasons and factual feature construction, not ranking:

```python
attainable = {g.skill_id: max(0, min(current.get(g.skill_id, 0) + g.gain,
                                   g.max_level) - current.get(g.skill_id, 0))
              for g in event.develops_skills}
counts = {s: sum(row.status == s for row in history)
          for s in ('completed', 'no_show', 'declined', 'dropped')}
# Include event-specific counts and matching record IDs; retain per-event
# facts so a future scorer can group related activities without reparsing files.
```

- [ ] Join eligible candidates into trajectory using the configured recurring policy; default frozenset({'EV_036'}) is documented starter-kit policy. No hardcoded employee IDs. Run Tasks 1–4 GREEN. Commit `feat: prepare eligible activities and recommendation evidence`.

## Task 5: Enforce authorization and expose the read-only API

**Create:** backend/app/core/{config,auth,errors}.py; backend/app/services/dataset.py; backend/app/api/{dependencies,employees}.py; backend/app/main.py; backend/tests/test_api.py. **Modify:** backend/app/schemas/responses.py, backend/tests/conftest.py.

**Consumes:** Task 1–4 contracts. **Produces:** Settings(raw_dir, state_path, allowed_origin, dev_identities, application_date); Principal; DomainError(code, message, details); create_app; dependencies require_hr, require_employee_access and require_self; GET /health, /api/employees, /api/employees/{id}, /trajectory. Token lookup maps to a server-owned principal. State persistence joins lifespan at Task 7.

- [ ] Write API tests using TestClient with lifespan, temporary source files and tokens `test-self`, `test-other`, `test-hr` mapped to test identities. Run `python -m pytest tests/test_api.py -q` RED:

```python
def test_foreign_employee_forbidden(api_client):
    response = api_client.get('/api/employees/OTHER_EMP',
                              headers={'Authorization': 'Bearer test-self'})
    assert response.status_code == 403
    assert response.json()['error']['code'] == 'forbidden'
```

- [ ] Add test_health_is_public; test_missing_and_unknown_token_401; test_spoofed_role_header_ignored; test_employee_list_contains_only_self; test_hr_can_read_any_profile; test_authorized_missing_employee_404; test_trajectory_contains_projected_skills_gaps_and_candidates; test_private_responses_no_store; test_invalid_request_redacts_input; test_earlier_application_date_rejected; test_bad_source_prevents_startup. A Principal linked to a nonexistent employee is rejected, not granted access to supplied path IDs.
- [ ] Implement dependencies before resource reads and a single domain-error adapter. Return request-scoped captured snapshots; business routes delegate. Use the exact approved response envelopes. Sanitize Pydantic errors to location/type/message, dropping input and sensitive context.

```python
def enforce_employee_access(principal: Principal, employee_id: str) -> None:
    if principal.role != 'hr' and principal.employee_id != employee_id:
        raise DomainError('forbidden', 'Access denied', [])

@router.get('/{employee_id}/trajectory', response_model=Trajectory)
def trajectory(employee_id: str, context=Depends(employee_read_context)):
    return build_trajectory(employee_id, context.snapshot, context.as_of_date)
```

Define employee_read_context in dependencies.py to return the authorized Principal, captured snapshot and effective date. Create simple dataclass RequestContext there; do not leave the route dependent on an undefined adapter.

- [ ] Run all existing tests GREEN. Start from backend/: `python -m uvicorn app.main:app --port 8000`; in another terminal verify `Invoke-RestMethod http://localhost:8000/health` and authorized employee/trajectory reads with configured demo tokens. Stop only the process started for this check. Commit `feat: expose authorized employee development API`.

## Task 6: Thin frontend vertical slice — no polishing

**Create:** frontend/package.json, package-lock.json, tsconfig.json, next-env.d.ts, next.config.ts, postcss.config.mjs; frontend/src/app/{layout.tsx,globals.css,page.tsx,employee/[id]/page.tsx}; frontend/src/lib/{api.ts,types.ts}; frontend/src/components/{session-provider.tsx,employee/profile.tsx,employee/trajectory.tsx,ui/status-message.tsx}. **No backend modifications.**

**Consumes:** Task 5 public contracts. **Produces:** API client methods listEmployees(token, signal), getEmployee(id, token, signal), getTrajectory(id, token, signal); matching TypeScript interfaces; a memory-only SessionProvider. Use Next.js/React/TypeScript/Tailwind versions verified together at execution time; package-lock.json pins the result. package scripts: dev, build, start, typecheck (`tsc --noEmit`).

- [ ] Initialize the minimal Next project in frontend without extra UI libraries. Implement the single request function and error model, then plain pages. App Router page params follow the installed Next version's type contract; keep data-fetching displays in client components.

```typescript
const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
export async function request<T>(path: string, token: string,
  init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${base}${path}`, { ...init, headers, cache: 'no-store' });
  const body = await response.json();
  if (!response.ok) throw new ApiError(response.status, body.error);
  return body as T;
}
```

Define ApiError(status: number, error: {code: string; message: string; details: unknown[]}) in api.ts. Use encodeURIComponent on resource IDs. No token in environment/browser persistence. Session change clears displayed data and increments a session generation; abort old requests and ignore results whose captured generation differs.

- [ ] Verify from frontend/: `npm run typecheck` and `npm run build`. This is a reversible UI shell, so do not add a UI testing library solely for rendering tests.
- [ ] Browser checks against the running real backend: enter the employee token, open profile, verify projected skills/next-grade gaps/candidates; enter HR token and inspect a second profile; try foreign profile as employee and see a permission error. Under browser network throttling, start profile load as HR, immediately change to employee token, and confirm old profile data never appears. Use offline mode to verify a clear retryable error, not a blank page.
- [ ] Commit `feat: add minimal employee trajectory frontend`. Stop styling once those checks pass; no chart or dashboard polish.

**Checkpoint B — first working demo:** real employee -> authorized API -> current skills -> next-grade gaps -> eligible activities -> frontend. This intentionally moves a thin read API/frontend ahead of mutations, as requested. Full API wiring and frontend mutation controls remain later tasks.

## Task 7: One validated state file and atomic replacement

**Create:** backend/app/schemas/state.py, backend/app/repositories/state.py, backend/tests/test_state.py. **Modify:** backend/app/services/dataset.py, backend/app/repositories/dataset.py, backend/app/schemas/responses.py, backend/app/main.py, backend/app/core/config.py, backend/tests/conftest.py.

**Consumes:** SourceBundle and build_snapshot. **Produces:** RuntimeCompletion(command_id, employee_id, event_id, source_record_id, participation_date, completed_on); CompletionReceipt(request_fingerprint, result); MutableState as shared vocabulary; StateRepository; DatasetService.commit. Define SkillChange(skill_id, before, after, gain) and CompletionResult(command_id, employee_id, event_id, skill_changes, trajectory, revision, as_of_date) in responses.py now so receipts are fully typed from their first use. Task 8 implements the command behavior. Add runtime_completions: tuple[RuntimeCompletion, ...] to DatasetSnapshot and an optional same-named argument to build_snapshot, defaulting to (). Store the snapshot class in repositories/dataset.py alongside its constructor; it is not a source-file envelope.

- [ ] Add and run `python -m pytest tests/test_state.py -q` RED:

```python
def test_failed_replace_preserves_file(state_repository, initial_state, monkeypatch):
    state_repository.save(initial_state)
    before = state_repository.path.read_bytes()
    def fail_replace(*args):
        raise OSError('simulated disk failure')
    monkeypatch.setattr('app.repositories.state.os.replace', fail_replace)
    with pytest.raises(OSError):
        state_repository.save(initial_state.model_copy(update={'revision': 1}))
    assert state_repository.path.read_bytes() == before
```

- [ ] Add test_missing_state_starts_empty; test_invalid_json_fails_startup; test_raw_fingerprint_mismatch_fails; test_roundtrip_state; test_failed_save_does_not_publish_snapshot; test_noop_does_not_increment_revision. Define state_repository as StateRepository(tmp_path / 'state.json') and initial_state as schema_version=1, fingerprint from the temporary raw fixture, revision=0 and empty imports/completions/receipts. dataset is a DatasetService assembled over these fixtures. Use the four raw hashes sorted by filename to compute a stable fingerprint. Raw file hash reads stay in DatasetRepository.
- [ ] Implement one atomic-write helper in StateRepository. Create a sibling temporary file, serialize the entire validated state, flush/fsync, close and replace. Clean up temporary files on failure. No backup/journal/retry machinery.

```python
with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
        dir=self.path.parent, delete=False) as stream:
    temporary = Path(stream.name)
    stream.write(state.model_dump_json())
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temporary, self.path)
```

- [ ] Add one threading.Lock to DatasetService. Callers acquire it, build next state using the latest state/snapshot, then call commit; commit validates and prepares the snapshot (including that revision's runtime_completions), saves state, and only then swaps the in-memory references. Sync mutations run in FastAPI's worker thread so request cancellation cannot interrupt a half-finished critical section. Readers capture one published snapshot. Add test_captured_snapshot_retains_old_runtime_after_commit: hold an old snapshot, commit a new runtime entry and assert the old tuple/revision remain unchanged while a fresh capture contains the entry. Verify config documents one Uvicorn worker.
- [ ] Run Task 7 GREEN and existing tests. Commit `feat: persist validated overlay with atomic replacement`.

**Time guard:** stop persistence work after the listed tests pass. No process-kill matrix, cross-process lock, background compaction or filesystem abstraction.

## Task 8: Idempotent completion with durable receipts

**Create:** backend/app/services/completion.py, backend/app/api/activities.py, backend/tests/test_completion.py. **Modify:** backend/app/schemas/{responses,state,history}.py, backend/app/services/{progress_engine,trajectory,dataset}.py, backend/app/main.py, backend/tests/conftest.py.

**Consumes:** principal, command and snapshot/state contracts, including SkillChange and CompletionResult from Task 7. **Produces:** CompletionCommand(command_id: UUID, source_record_id: str | None = None, session_date: date | None = None); complete_activity and POST completion. Receipt holds the exact typed result. project_skills remains unchanged; effective_history(snapshot: DatasetSnapshot, employee_id: str) -> list[ParticipationView], in progress_engine.py, replaces a transitioned source participation with one effective completion. Trajectory/profile/HR consumers use this same adapter and the captured snapshot's runtime tuple.

- [ ] Add fixtures complete_args (authorized TEST_EMP, EV_012, fixed UUID, no source record, clock 2026-10-01) and restart_dataset (loads the same temporary raw/state paths). Run `python -m pytest tests/test_completion.py -q` RED:

```python
def test_retry_after_restart_returns_receipt(complete_args, restart_dataset):
    first = complete_activity(**complete_args)
    restarted = restart_dataset()
    retry = complete_activity(**{**complete_args, 'dataset': restarted})
    assert retry == first
    assert restarted.capture().revision == 1
    assert len(restarted.state.completions) == 1
```

- [ ] Add test_changed_command_with_same_id_conflicts; test_different_id_same_nonrecurring_event_conflicts; test_same_source_record_cannot_complete_twice; test_source_transition_contributes_once; test_recurring_same_session_conflicts; test_recurring_distinct_sessions_gain_once_each; test_future_session_rejected; test_unknown_session_rejected; test_self_paced_cannot_be_backdated; test_existing_record_must_be_in_progress_or_overdue; test_other_employee_and_hr_denied; test_unknown_event_404; test_existing_assignment_can_finish_without_current_prerequisite; test_mandatory_completion_uses_only_declared_gains; test_source_record_wrong_event_rejected. Verify resulting trajectory/current_skills, not just row counts.
- [ ] Implement the smallest locked command path:

```python
with dataset.lock:
    # Authorize before reading receipts or resource details.
    fingerprint = normalized_command_fingerprint(principal, employee_id, event_id, command)
    prior = dataset.state.receipts.get(str(command.command_id))
    if prior is not None:
        if prior.request_fingerprint != fingerprint:
            raise DomainError('conflict', 'Command ID already used', [])
        return prior.result
    # Validate participation; construct next completion/state and prospective
    # trajectory, store its receipt, then commit once. No in-place skill edits.
```

Define normalized_command_fingerprint privately in completion.py using canonical JSON of principal, resource IDs and validated command fields. Normalize dates/defaults before hashing. No secret token is stored. Check semantic duplication independently from the request UUID. Reject conflicting session_date when source_record_id supplies a participation date. Runtime completed_on is the effective clock, not the historical enrollment date.

- [ ] Add test_two_simultaneous_identical_commands_apply_once using ThreadPoolExecutor(2) and a Barrier, then assert both results equal and revision=1. Add test_save_failure_then_retry_applies_once by injecting one StateRepository.save failure and checking no in-memory gain before retry. One focused concurrency test suffices here; no stress framework.
- [ ] Run completion/projection/API tests GREEN, then full backend suite. Commit `feat: complete activities idempotently without raw mutations`.

## Task 9: Whole-import validation and deterministic collisions

**Create:** backend/app/api/dataset.py, backend/tests/test_import.py. **Modify:** backend/app/services/dataset.py, backend/app/repositories/dataset.py, backend/app/schemas/responses.py, backend/app/main.py, backend/tests/conftest.py.

**Consumes:** parse_employees/parse_history, principal, source bundle and state. **Produces:** import_dataset as shared vocabulary; ImportResult(added_employees, unchanged_employees, added_history, unchanged_history, revision, as_of_date); HR-only multipart POST import with optional employees/history file parts. No catalog replacement, ZIP or path imports.

- [ ] Add import fixtures new_employee (unique ID, known role/skills, existing valid manager or null), new_history referencing that employee and a known event, and bad_history pointing to an unknown event. Run `python -m pytest tests/test_import.py -q` RED:

```python
def test_invalid_history_rolls_back_employee(hr, new_employees_document,
        bad_history, dataset):
    before = dataset.capture()
    state_before = dataset.state.model_dump_json()
    with pytest.raises(DomainError):
        import_dataset(hr, new_employees_document, bad_history, dataset)
    assert dataset.capture() is before
    assert dataset.state.model_dump_json() == state_before
    assert dataset.capture().employees.get('JURY_NEW') is None
```

- [ ] Add test_identical_reimport_is_noop; test_changed_existing_employee_or_history_409; test_duplicate_id_inside_upload_422; test_new_id_same_participation_409; test_second_completed_nonrecurring_event_409; test_unknown_cross_reference_422; test_new_employees_can_reference_each_other (valid managers); test_employee_only_and_history_only_import; test_metadata_mismatch_422; test_blank_optional_csv_and_bom; test_completed_before_review_is_not_replayed; test_reimport_source_after_runtime_transition_keeps_one_gain; test_import_conflicting_runtime_participation_409; test_late_invalid_row_preserves_raw_hashes_and_state_file; test_failed_persistence_no_publication.
- [ ] Implement normalized source equality before any runtime projection. Build the complete merged SourceBundle and overlay under dataset.lock. Run shared validation, then save once. For exact reimports return counts with unchanged revision. Unknown fields, date/status/range failures and references return 422; source-ID or semantic participation conflicts return 409.

```python
existing = source_records.get(incoming_id)
if existing is not None:
    if existing.model_dump(mode='json') != incoming.model_dump(mode='json'):
        raise DomainError('conflict', 'Existing ID has different content', [])
    unchanged += 1
else:
    additions.append(incoming)
# Do not publish additions until all records and merged references validate.
```

- [ ] Add test_concurrent_import_and_completion_preserve_both using two distinct operations and the shared lock, asserting revision=2 and both effects after restart. Add test_no_payload_422, test_employee_cannot_import_403 and test_upload_limit_413 to API tests. Bound streamed request bytes, including multipart overhead, at 10 MiB before full buffering; a small ASGI receive wrapper in api/dataset.py scoped to the import route is sufficient. Also cap bytes read from UploadFile. Do not rely solely on Content-Length or post-parse checks. Inspect authorization from request headers before parsing the body; test chunked/missing Content-Length with invalid trailing bytes and no mutation.
- [ ] Run import/state/completion/API tests GREEN. Commit `feat: import jury profiles and history atomically`.

## Task 10: Complete API contracts and preserve the AI seam

**Create:** backend/app/services/recommendation_engine.py, backend/app/ai/{client,recommender}.py, backend/app/api/recommendations.py, backend/tests/test_recommendation_boundary.py. **Modify:** backend/app/schemas/recommendation.py, backend/app/main.py, backend/tests/test_api.py, frontend/src/lib/types.ts only to reconcile public DTO declarations if needed (coordinate with frontend owner).

**Consumes:** factual candidates from Task 4. **Produces:** AIRefinementInput(employee_id, current_grade, targets, candidates, revision, as_of_date); RecommendationItem(event_id, explanation, evidence: list[RecommendationFactor]); RecommendationResult(status: Literal['success', 'no_candidates'], employee_id, recommendations: list[RecommendationItem], revision, as_of_date); AIClient Protocol with refine(context: AIRefinementInput) -> RecommendationResult; DisabledRecommender; validate_recommendation_result(context, result) -> RecommendationResult. Success requires 1–3 items; no_candidates requires an empty list and no eligible inputs. Require matching employee/revision/as_of_date, distinct allowed event IDs and exact supported evidence values with at least three distinct factor kinds per item. Engine recommend(employee_id, snapshot, as_of_date) raises recommendations_not_implemented. No SDK, network connection, prompts or weights.

- [ ] Add and run `python -m pytest tests/test_recommendation_boundary.py tests/test_api.py -q` RED:

```python
def test_recommendation_route_is_honestly_unimplemented(api_client):
    response = api_client.post('/api/employees/TEST_EMP/recommendations',
        headers={'Authorization': 'Bearer test-self'})
    assert response.status_code == 501
    assert response.json()['error']['code'] == 'recommendations_not_implemented'
```

- [ ] Add test_auth_before_recommendation_lookup; test_candidate_has_all_nine_requested_fact_groups; test_output_rejects_invented_event; test_output_rejects_duplicate_event; test_output_requires_one_to_three_for_success; test_output_requires_three_distinct_supported_factors; test_output_rejects_changed_fact_values; test_no_candidate_is_distinct_status. Use fabricated provider output only inside these unit tests, never as an endpoint result. Selected evidence references must resolve back to candidate facts; carry structured factors by reference rather than allowing LLM-authored numeric facts to replace them.
- [ ] Implement the protocol and disabled implementation:

```python
class AIClient(Protocol):
    def refine(self, context: AIRefinementInput) -> RecommendationResult: ...

class DisabledRecommender:
    def refine(self, context: AIRefinementInput) -> RecommendationResult:
        raise DomainError('recommendations_not_implemented',
                          'AI recommendations are not implemented', [])
```

The Protocol ellipsis is a Python abstract contract, not an unfinished implementation. Future prose remains model output requiring evidence checks; do not claim structured validation proves arbitrary prose truthful. Return no AI result now.

- [ ] Verify all implemented endpoints against spec §9: response models, status codes 401/403/404/409/413/422/501/503, private no-store headers and redacted errors. Add test_openapi_has_all_current_routes and test_request_validation_uses_error_envelope. HR route is added in Task 11; the assertion expands there. Run GREEN. Commit `feat: define validated recommendation boundary without AI calls`.

## Task 11: Minimal HR aggregates

**Create:** backend/app/services/hr.py, backend/app/api/hr.py, backend/tests/test_hr.py. **Modify:** backend/app/schemas/responses.py, backend/app/main.py, backend/tests/test_api.py.

**Consumes:** snapshot, effective histories, trajectory and eligibility. **Produces:** build_hr_dashboard; HRDashboard(skill_gap_counts, participation_by_event, employees_without_candidate, recommendation_status, employees_without_recommendation, revision, as_of_date). SkillGapCount(skill_id, name, employee_count); ParticipationCount(event_id, title, status_counts); lists are sorted deterministically by ID. No employee performance ranking.

- [ ] Add and run `python -m pytest tests/test_hr.py tests/test_api.py -q` RED:

```python
def test_recommendation_coverage_is_unknown(dataset, clock):
    result = build_hr_dashboard(dataset.capture(), clock)
    assert result.recommendation_status == 'not_implemented'
    assert result.employees_without_recommendation is None
```

- [ ] Add test_gap_counts_count_employees_not_gap_levels (two employees deficit1/3 ->count2); test_lead_excluded_from_next_grade_gap_counts; test_participation_transition_counted_once (in_progress ->completed, not both); test_no_candidate_does_not_claim_no_recommendation; test_import_and_completion_update_aggregates; test_employee_hr_route_403; test_hr_dashboard_200. Expand OpenAPI route coverage to all eight approved endpoints.
- [ ] Implement one pass over each employee's deterministic trajectory and effective history, accumulating counters. No analytics cache or background job:

```python
for gap in trajectory.next_grade_gaps:
    if gap.gap > 0:
        counts[gap.skill_id] += 1
if not trajectory.candidates:
    employees_without_candidate.append(employee.employee_id)
```

- [ ] Run GREEN and full backend suite. Commit `feat: expose authorized HR development aggregates`.

**Checkpoint C:** backend foundation complete, including import, progress, authorization and explicit recommendation boundary. Future scoring can consume candidates without touching source parsers or API authorization.

## Task 12: Minimal mutation and HR controls

**Create:** frontend/src/app/hr/page.tsx, frontend/src/components/hr/dashboard.tsx. **Modify:** frontend/src/lib/{api,types}.ts; frontend/src/components/employee/{profile,trajectory}.tsx; frontend/src/app/page.tsx as needed for navigation. No styling redesign.

**Consumes:** completion/import/HR contracts. **Produces:** completeActivity(id, eventId, command, token), importDataset(files, token), getHRDashboard(token) in api.ts; TypeScript mirrors for their DTOs. Keep request helper the single URL/auth/error layer.

- [ ] Add the small command/form adapters:

```typescript
const form = new FormData();
if (employees) form.append('employees', employees);
if (history) form.append('history', history);
return request<ImportResult>('/api/dataset/import', token,
  { method: 'POST', body: form });
// Do not set Content-Type: the browser must supply the multipart boundary.
```

Completion generates crypto.randomUUID() once per intentional operation, retains command/body for retry on uncertain network failure, disables simultaneous submission and refetches profile/trajectory after success. Offer completion only for currently completable participations or self-paced candidates; future sessions are displayed with dates and are not marked complete. A source record carries its ID into the command. Do not display optimistic skill changes.

- [ ] Add plain HR count tables, recommendation-unavailable text and two labeled file inputs. Render row/field errors without dumping the uploaded content. Refresh HR results after successful import. Unknown tokens and employee tokens still receive backend errors at /hr.
- [ ] Run `npm run typecheck` and `npm run build`. Browser smoke: self-paced completion raises expected levels; retry preserves result; HR can import a new profile/history and open its trajectory; invalid history plus new profile leaves it absent; employee cannot import; HR cannot complete; recommendation action clearly says unavailable. Repeat the Task 6 identity-switch check with a mutation response in flight.
- [ ] Commit `feat: add minimal completion and HR import controls`.

## Task 13: One-command launch and accurate documentation

**Create:** frontend/Dockerfile, frontend/.dockerignore; backend/Dockerfile, backend/.dockerignore; docker-compose.yml, .env.example, docs/architecture.md, docs/data-model.md. **Modify:** README.md, .gitignore, frontend/next.config.ts (standalone output), backend/app/core/config.py only if required to align environment names. Preserve existing README attribution.

**Consumes:** working local applications. **Produces:** reproducible two-container local launch with no AI keys or external state service required.

- [ ] Configure Next standalone output and a multi-stage npm-ci/build/runtime image; backend image installs pinned requirements and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`. Use Python urllib for healthcheck instead of adding curl. Avoid running install/build tests against source data writable mounts.

```yaml
# Required Compose topology (merge into complete service definitions):
services:
  backend:
    ports: ["127.0.0.1:8000:8000"]
    volumes:
      - ./data/raw:/app/data/raw:ro
      - career_quest_state:/app/data/state
  frontend:
    ports: ["127.0.0.1:3000:3000"]
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}
volumes:
  career_quest_state:
```

Include backend build context ./backend, effective raw/state paths, allowed origin, explicit public demo token mapping and frontend depends_on backend service_healthy. The frontend runtime must listen on 0.0.0.0 inside its container. API URL is a frontend build argument, not only a runtime environment value. Development token examples may reference a supplied employee; domain code may not.

- [ ] Write README setup, environment variables, local venv/npm commands, `docker compose up --build`, endpoint table, data/archive placement, test commands, exact status and next recommendation milestone. Explain public demo credentials, enforced permissions, production authentication exclusion, frozen dataset clock, advancing demo date, one-worker limit, atomic/no-op/conflict import rules and state reset with raw data preserved. Document named-volume persistence; do not instruct destructive reset as the normal launch command.
- [ ] Write architecture.md and data-model.md from the implemented interfaces, including the future pipeline and all evidence fields. Document the recurring-club exception and assessment-date approximation. Include Mermaid/text diagrams only where they explain data flow; no new infrastructure.
- [ ] Run root `docker compose config --quiet`; inspect resolved config locally without publishing credentials. Run `docker compose up --build -d`, then `docker compose ps`, GET /health and browser open localhost:3000. Restart backend and check imported data/completion remains. If Docker is unavailable, record the exact blocker and leave container-start verification unpassed.
- [ ] Commit `docs: document and containerize Career Quest foundation`.

## Task 14: Verify foundation and hand off to recommendation work

**Create:** docs/handoff.md. **Modify:** README.md and docs/{architecture,data-model}.md only for discrepancies uncovered by verification. Correct functional findings in their owning files with regression tests; no speculative changes.

**Consumes:** all prior deliverables. **Produces:** evidence-backed handoff and clear next-milestone interface map.

- [ ] Run from backend/: `python -c "from app.main import create_app; print('backend import OK')"` and `python -m pytest tests -q`. Recheck raw SHA-256 manifest. Do not claim a test ran based on plan snippets.
- [ ] Run from frontend/: `npm ci`, `npm run typecheck`, `npm run build`. Run root `docker compose config --quiet` and the live startup checks from Task 13. Repeat only after changes/failures justify it; avoid rebuilding repeatedly after unchanged successful checks.
- [ ] Smoke the complete demo with unfamiliar fixture IDs: HR imports a valid employee and history, employee credentials configured for that identity access only their data, skills/gaps/candidates render, completion changes the projection once, restart preserves it, HR aggregates reflect it. Negative checks: foreign profile denied; employee import denied; conflicting import leaves state unchanged; recommendations return 501. Record a representative local read response below the two-second target or a measured failure, without production latency claims.
- [ ] Review Git diff, raw hashes and staged filenames for accidental source mutation, real credentials, .env, runtime state or dependency/build output. Run `git diff --check`. Verify all file access remains in repositories and no component hardcodes a backend URL. Review whether required DTOs/evidence survive through the client and whether README matches tested commands.
- [ ] Perform the selected execution workflow's code-review gate. Resolve actionable correctness findings and rerun affected checks. Do not invoke that execution workflow during this planning turn.
- [ ] Write docs/handoff.md with actual final tree/files, launch/test commands, measured outcomes, explicit unverified checks, one-process/demo-auth limits and AI-unimplemented status. Make the next task “multi-factor recommendation scoring and LLM refinement” and link the exact schemas/recommendation.py, services/eligibility.py, services/recommendation_engine.py and ai interfaces.
- [ ] Commit `docs: record foundation verification and recommendation handoff`. Deliver actual results, not this plan's expected results.

## Recommendation milestone handoff contract

Foundation verification unlocks the following work immediately; these are boundary requirements, not authorization to implement it in this plan:

1. Capture revision/as_of_date and current employee state from DatasetService.
2. Use next-grade and separately labeled career-goal TargetAnalysis outputs.
3. Consume eligible RecommendationCandidate objects, preserving exclusions.
4. Score multiple deterministic facts: current/target grades, skill current/required levels, criticality, capped gains, completed history, no-shows/declines/drops and availability. History facts retain record/event IDs for grouping related activities.
5. Give the LLM only allowed candidates and verified facts; return references to those facts with explanatory prose.
6. Validate 1–3 distinct eligible events and supporting evidence. Do not accept invented skills, requirements, gains or progress from the model. Recompute or reject against a changed dataset revision rather than presenting stale eligibility as current.
7. Replace the explicit 501, then populate HR recommendation coverage. Test unfamiliar multifactor scenarios, not only lowest-skill examples; implement the ten-second AI latency budget there.

Do not add numeric scoring weights or provider calls to “help” this foundation. The highest-priority next investment is recommendation quality, not UI refinement or extra persistence mechanics.

## Sequence, parallel work and checkpoints

| Wave | Tasks | Exit condition |
| --- | --- | --- |
| A | 1 -> 2 -> 3 -> 4 | Real loading, projection, gaps, eligibility and evidence tested |
| B | 5 -> 6 | Authorized read API and employee page form a working demo |
| C | 7 -> 8 -> 9 | One durable overlay, correct completions and jury imports |
| D | 10 -> 11 -> 12 | Full foundation API/HR and basic mutation UI |
| E | 13 -> 14 | Reproducible verified foundation and recommendation handoff |

Task numbers are estimates of implementation order, not rigid requirements to delay independent work. After Task 5 freezes read DTOs, Task 6 frontend work can run alongside Task 7 backend persistence, with disjoint file ownership. After Task 4, Task 10's schemas/AI-contract work can be prepared in parallel only if one designated owner controls shared recommendation DTOs and main.py wiring. After Task 11 freezes HR/import/completion responses, Task 12 frontend work can run alongside Task 13's backend Docker/documentation work; frontend package/config/Docker edits need coordination. Keep Tasks 7–9 with one owner because they share the state invariant. Do not parallelize initial schema/trajectory/candidate contracts or independently edit shared response models.

Critical path to the first demo: **1 -> 2 -> 3 -> 4 -> 5 -> 6**. Critical path to a jury-import/completion demo adds **7 -> 8 -> 9 -> 11 -> 12**, with Task 10 supplying honest AI status, then reproducibility checks in 13–14. No wall-clock completion promise: dependency installation and Docker availability are not yet verified. The small frontend slice is intentionally the only departure from the user's numbered order and follows their explicit request to demonstrate reads before mutation/import.

Recommended execution method: **Native**, keeping the tightly coupled backend contracts under one implementer and using the workflow's final independent review. Subagent-driven execution is also supported after explicit selection, but per-task context/review overhead is significant for this small integrated foundation. Parallel-safe opportunities above do not authorize delegation on their own.

## Plan self-review and stop condition

- Spec coverage: tree/boundaries 1–13; source/domain models 1–4; authorization 5/8–11; state 7–9; API 5/8–11; frontend 6/12; recommendation/AI boundary 4/10; Docker/docs 13; verification/handoff 14.
- Review Focus conditions each have an explicit test or browser check in the named owning task.
- Type/ownership check: projection and source repository interfaces stay stable; runtime history is adapted once; imports compare immutable rows; frontend reads public DTOs; shared file changes are sequenced.
- Scope check: no scoring, provider calls, design polish, database, enterprise auth or generalized durability subsystem.
- This is a written plan only. No product files were created, tests executed, dependencies installed or execution skills invoked during planning.
- **STOP:** present this plan for approval and ask the user to choose Native or Subagent-driven execution. Do not start Task 1 until that approval and choice arrive.
