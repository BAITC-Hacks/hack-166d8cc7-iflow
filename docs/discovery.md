# Career Quest discovery — 2026-09-23

Status: discovery complete; design and implementation pending. No product code or raw data has been changed.

## Sources inspected

- Local four-page hackathon PDF supplied by the user: `C:/Users/zhasy/Downloads/HackAlem AI_ Career Quest - платформа геймификации жизненного цикла сотрудника..pdf`.
- Primary Drive URL could not be read through the web tool; equivalence to the local PDF is not independently verified.
- Starter kit found at `C:/Users/zhasy/Downloads/career_quest_dataset.zip`, under `case_1/career_quest_dataset/`. Read its English README, JSON envelopes and representative records, field unions, CSV headers and status counts without extracting or modifying the archive.
- Repository initially contains only README.md, with no application, dataset, or AGENTS.md.

## Case 1 requirements

The final hackathon application must show an employee's role, grade, skills, completed activities and career trajectory; recommend 1–3 relevant activities with explanations using at least three factors; update progress after completion; and provide HR views of frequent skill gaps, employees without recommended steps, and participation by activity.

Inputs are employee, event and skill JSON files and participation CSV. Outputs are profile/trajectory, explainable recommendations, updated skill progress and HR summaries. Additional jury profiles and history must load using the same schema.

Constraints: UI response at most two seconds and recommendation response at most ten seconds; one-command startup; employee/HR permission separation; engagement information private from other employees without consent; synthetic data must remain within the hackathon. No real personal data, public employee rankings, mandatory-process reward mechanics, or single-factor rules represented as AI. Gamification and localization are optional.

Jury checks: open an arbitrary employee; inspect 1–3 recommendations and at least three explanatory factors; complete an activity and observe changed progress/trajectory; inspect HR summaries; upload unfamiliar profiles/history. Three shared evaluation profiles deliberately defeat lowest-skill-only logic, including repeated skipped activities competing with a promotion-critical skill.

Deliverables: repository and README with reproducible launch and verification instructions. Evaluation: functionality 25, technical implementation 25, README/reproducibility 25, value/applicability 15, development potential/originality 10.

The current requested milestone is only the architecture, data layer, deterministic services and minimal application skeleton. Deferred AI must be explicitly marked unavailable; this milestone is not a completed hackathon submission.

## Observed starter-kit schema

All JSON files have `meta` with dataset, version and as_of_date. Snapshot date is `2026-10-01`, explicitly treated as today. History spans `2024-10-01` to `2026-09-30`.

- `employees.json`: `employees` array, 200 records. Fields: employee_id, full_name, department, role, grade, manager_id (nullable), hire_date, tenure_months, work_format, preferred_language, career_goal (nullable target_role/target_grade), skills, last_review_date.
- `events.json`: `events` array, 40 records. Fields: event_id, title, description, type, format, duration_hours, mandatory, target_roles, target_grades, develops_skills (skill_id/gain/max_level), prerequisites, upcoming_sessions.
- `skills.json`: proficiency_scale, 60 skills, 32 role_profiles. Skill fields: skill_id, name, type, category, description. Role profile fields: role, grade, required_skills, critical_skills. Grade order: Junior, Middle, Senior, Lead.
- `activity_history.csv`: 2,743 records. Columns: record_id, employee_id, event_id, date, due_date, status, completion_pct, score, feedback_rating, assigned_by. Empty optional dates/numbers must parse as null.
- Status counts: completed 2,178; no_show 195; dropped 160; declined 104; overdue 90; in_progress 16.

## Rules that affect architecture

1. Missing skills mean level zero; proficiency is 0–5.
2. Employee skills are the last assessment, not necessarily current. Apply completed history strictly after last_review_date in chronological order. Do not replay older history or apply the same completion twice.
3. Completion adds gain up to the event's max_level. An activity whose cap is below an already-held skill must not reduce the skill.
4. Mandatory activities are not recommendation targets.
5. Eligibility must consider audience and prerequisites. Self-paced activities have no sessions and are always available; scheduled availability uses the dataset snapshot clock.
6. Completed events cannot repeat except EV_036, a documented recurring club. This is a dataset policy exception, not permission to hardcode employee identities or jury profiles.
7. Preserve original JSON/CSV bytes. Keep imports and new completions separate from raw data.
8. Keep next-grade requirements distinct from an explicit career goal, particularly cross-role goals and employees already at Lead.

## Proposed design for review

Use the existing repository root as the project root rather than adding a redundant career-quest directory. Keep frontend/, backend/, data/ and docs/ as requested.

Recommended approach: FastAPI with validated in-memory dataset snapshots loaded through concrete repositories, pure deterministic services, and a separate local JSON state file for imports/completions. Validate a prospective import fully before replacing the active snapshot. Keep file IO in repositories, coordinate mutation through one service, and explicitly run one backend worker for the file-backed MVP. Next.js uses a single typed API client and minimal employee/HR pages. Recommendation API returns a documented unimplemented response while typed factors/candidates/results establish the future contract.

Alternatives: an entirely in-memory overlay is simpler but loses completions on restart; a database adds avoidable infrastructure at this scale. File-backed state is the proposed middle ground. No agent framework, AI SDK, database, generic repository framework, or elaborate UI is needed.

Boundaries: schemas define source and API contracts; repositories own decoding, immutable source loading and overlay persistence; services own current-skill projection, gaps, trajectory, eligibility and completion; routes handle HTTP only; ai/ contains future provider contracts. Add a dataset schema and repository/coordinator because import validation spans all four input files. Avoid empty modules created only to match a diagram.

Before implementation, resolve the concrete employee/HR access boundary and import collision/idempotency behavior in the written design. Permission separation is required by the source specification and cannot be represented by unprotected employee/HR page names alone.

Proposed implementation order after workflow approvals: source contracts and loading tests; deterministic projection/gap/progress tests and services; API and import/state behavior; minimal frontend and API types; Docker and documentation; full verification and handoff.

Verification must cover raw-file hashes, real dataset parsing and cross-references, gaps including Lead/missing skills, assessment-date replay, gain caps without regression, duplicate completion, missing IDs, rejected imports without partial mutation, API startup/health, frontend typecheck/build, and Compose validation.

## Workflow status and handoff

Read Superpowers using-superpowers, its Codex tool reference, and brainstorming instructions. This is an architectural task. The installed brainstorming skill requires design review, written-spec approval, then written-plan review and execution-method selection before implementation.

Searched accessible personal skills and plugin caches. Found caveman and Superpowers, but not the requested grill-with-docs, grill-me, handoff, implement or diagnosing-bugs skills. Do not claim to have used missing skills. grill-with-docs is explicitly required by the request, so obtain its actual SKILL.md location before claiming that stage complete.

Next action: locate grill-with-docs, validate these findings with its actual instructions, and complete Superpowers design review. No dependencies installed; no tests/builds/startup attempted; no product implementation exists yet.
