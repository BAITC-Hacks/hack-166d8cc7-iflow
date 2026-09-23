# Data model

The starter-kit files retain their original bytes and names. data/fixtures/raw-sha256.json records archive hashes. JSON envelopes include meta(dataset, version, as_of_date); the source clock is 2026-10-01. CSV history spans 2024-10-01 through 2026-09-30.

| File | Source content |
| --- | --- |
| employees.json | employee_id, full_name, department, role, grade, manager_id, hire_date, tenure_months, work_format, preferred_language, career_goal, skills, last_review_date |
| events.json | event_id, title, description, type, format, duration_hours, mandatory, target_roles, target_grades, develops_skills, prerequisites, upcoming_sessions |
| skills.json | proficiency_scale, skills (skill_id/name/type/category/description), role_profiles (role/grade/required_skills/critical_skills) |
| activity_history.csv | record_id, employee_id, event_id, date, due_date, status, completion_pct, score, feedback_rating, assigned_by |

Pydantic rejects unknown fields and invalid ranges/enums. Optional blank CSV date/numeric values become null. References are validated across the entire prospective bundle, including managers, role/grade targets and skill IDs. No fixed employee ID pattern or count is enforced.

## Deterministic projection

Missing skill means zero. For completed history strictly after last_review_date and no later than the effective clock, apply gains chronologically, then stable completion ID. CSV has no completion timestamp: historical date is the documented approximation. Runtime transitions have an explicit completed_on date.

new = max(current, min(current + gain, max_level)) prevents lower-cap activities from reducing existing proficiency. Levels are 0–5; incomplete/no-show/declined/dropped/overdue rows do not contribute. Runtime completion of an in_progress/overdue source row replaces its effective status, without rewriting it or counting it twice.

gap = max(required - current, 0). Next grade follows Junior -> Middle -> Senior -> Lead. Lead has no next grade. An explicit cross-role career goal is analyzed independently. Coverage caps each current skill at its requirement before dividing by total requirements; it is not an automatic promotion decision.

## Eligibility and source discrepancy

Voluntary recommendation candidates require role/grade fit, prerequisites, availability and an attainable target gain. Scheduled availability uses the dataset/application clock; self-paced events are always available. No-show/decline/drop history is evidence, not a permanent ban.

EV_036 is the documented recurring club. Actual source history also repeats annual mandatory compliance EV_001–003, although its README states a general no-repeat rule. Those original rows are preserved. Distinct existing compliance assignments may complete; imports accept distinct zero-gain compliance participations. Neither behavior recommends mandatory events or awards invented gains.

## Mutable overlay

state.json contains schema_version, raw_fingerprint, revision, imported_employees, imported_history, completions and receipts. Imports retain their source models. RuntimeCompletion contains command_id, employee_id, event_id, source_record_id, participation_date and completed_on. CompletionReceipt stores a canonical request fingerprint and the original typed result.

Source ID collision: identical normalized source content is unchanged; different content is a conflict. Participation identity is employee/event/date. Completion commands also enforce event non-repeatability and source-transition uniqueness independently of command IDs. One employee and invalid history in the same request rejects everything.

The state file does not store an authoritative mutable skill balance. The profile API returns both the immutable assessment and derived current_skills. Every read uses one captured dataset revision, including runtime history.

## Public outputs

EmployeeDetail combines profile/current_skills/effective history. Trajectory combines next grade, gaps, separate goal, coverage, completed activities and candidates. RecommendationFactor provides kind, scalar values and source IDs. HR counts skill-deficient employees and effective participation statuses; recommendation coverage remains explicitly unavailable.

See /docs for the executable OpenAPI models and README.md for command/import examples.
