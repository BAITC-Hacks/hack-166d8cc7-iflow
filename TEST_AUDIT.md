# Career Quest Independent QA Audit

## Environment

Audit date: 2026-09-23. Independent QA / red-team / jury role; no developer reasoning or implementation history received. Expectations derived first from Halyk Career Quest requirements and original dataset README. Current source inspected only to locate public entry points and test seams. Existing project tests were not used as proof of correctness.

Repository: `C:\Users\aser\hack-166d8cc7-iflow`. Windows, Python 3.13.14, FastAPI/Starlette TestClient, configured OpenAI `gpt-4.1-mini`. Business snapshot remains **2026-10-01**, not machine date. TestClient exercises the real ASGI routing/auth/multipart/schema/business/persistence path in an isolated local application instance, without a TCP server or browser.

Only new `tests/` artifacts and this report were written by this auditor. Production source, source data, `.env`, normal runtime state were not changed. Workers and automatic AI preparation were disabled, temporary state was deleted on exit, no mail endpoints or real SMTP sends were used. Temporary catalog copies were used only for documented controlled variants. An unrelated `frontend/next-env.d.ts` modification was reported by the coordinator; this auditor did not run Next/npm and did not touch that file. No commits/pushes.

Reproduction from repository root:

```powershell
python tests/independent_qa/run_all.py --live
```

The installed interpreter used here was `C:\Users\aser\AppData\Local\Programs\Python\Python313\python.exe`. Omit `--live` for deterministic/fake-provider checks. Each run uses disposable state. The suite caps provider calls at 35, below the authorized 40; no retry loops. This recorded audit used **21 actual live LLM calls, 20 successful model outputs, 1 provider-boundary validation error**. Model nondeterminism means future response content and totals can differ. `build_recorded_report.py` is a report formatter for this recorded human review, **not** an automated semantic oracle to apply to future outputs.

## Dataset validation

Five source artifacts (`employees.json`, `events.json`, `skills.json`, `activity_history.csv`, `README.md`) are byte-identical to the original `career_quest_dataset.zip`. Counts: 200 original employees, 40 events, 60 skills, 32 role/grade requirements, 2,743 original history records. Public import added **24 new synthetic employees and 41 history rows**, not source-code constants. Files: `tests/fixtures/jury_profiles/employees.json`, `activity_history.csv`, `manifest.json`.

Employee envelope is `meta + employees[]`; each employee contains ID/name/department/role/grade/manager, hire date/tenure, work format/language, nullable `career_goal`, skill map and last review date. Every synthetic manager references the existing Backend Lead. Skills deliberately mostly equal 5 to isolate adversarial gaps; this is valid but is a stress distribution, not a workforce prevalence estimate. JQA021 intentionally has empty history; other employees include first-month onboarding. Contrastive employees differ in identity to permit import but otherwise only the tested factor.

Events contain ID/title/description/type/format/duration, mandatory, role/grade audiences, `develops_skills` (`skill_id`, `gain`, `max_level`), prerequisites and upcoming sessions. Skill catalog contains scale 0-5 and role/grade required and critical sets. Missing employee skill means 0. Eligibility requires current role/grade audience and current prerequisite levels; career switching does not waive entry restrictions. Mandatory events are not personalized recommendations. Empty sessions are valid for self-paced only. Completion increases each skill by gain, capped at max_level, without reducing a level already above the cap. Completed activity is nonrepeatable except **EV_036** recurring club.

History columns are record/employee/event IDs, date, due_date, status, completion_pct, score, feedback_rating, assigned_by. Valid statuses: completed, in_progress, dropped, no_show, declined, overdue. The task's informal `missed` maps to `no_show`; `registered` is not a valid source status and correctly fails schema validation. Completed must be 100%; unfinished statuses do not add gains. Completed records strictly after last_review_date contribute to the snapshot; same-day assessment ordering is not defined intraday. Dataset uses date as session/enrollment date, so actual historical completion timestamp is not available.

Original catalog contains no exact attractive mandatory critical-design course and no single no-valid-activity profile with all four different exclusion reasons simultaneously. The original-catalog no-valid case JQA014 exhausts EV_006/007 and hits EV_005 cap; prerequisite/role traps are tested independently. A temporary schema-preserving mandatory EV_006 variant tests the attractive mandatory trap without altering production. A temporary scheduled EV_006 with no sessions tests unavailable activity. Critical-only pair modifies only Senior Backend critical flags, keeping required levels/employee/history/events unchanged.

## Tests executed

**TOTAL 160 = PASSED 142 + FAILED 15 + NOT VERIFIED 3.** These are assertion/review counts, not employee count or unique defect count. **Unique defects: 6 (CRITICAL 0, HIGH 4, MEDIUM 2, LOW 0).** One root defect can fail multiple independent checks. The single initial JQA004 503 is counted as an availability failure; its missing selection is NOT VERIFIED, not double-counted as evidence of bad ranking.

The complete unambiguous registry is `tests/independent_qa/results/registry-final.json` and the table below. `manual_review.json` binds all 20 recommendation reviews to hashes of the actual saved responses. Raw component registries retain original observations; final adjudication corrects the initially overstrict assumption that unknown imported profiles must automatically receive login credentials. README documents manual provisioning.

| ID | Check | Result | Evidence / limitation |
|---|---|---|---|
| D01 | Original archive integrity | PASSED | [] |
| D02 | 24 distinct schema-preserving synthetic profiles | PASSED | Full validity additionally checked by public import |
| I01 | Public multipart import of new employees and history | PASSED | {'added_employees': 24, 'unchanged_employees': 0, 'added_history': 41, 'unchanged_history': 0, 'revision': 1, 'as_of_date': '2026-10-01'} |
| I02 | Reimport is idempotent | PASSED | {'added_employees': 0, 'unchanged_employees': 24, 'added_history': 0, 'unchanged_history': 41, 'revision': 1, 'as_of_date': '2026-10-01'} |
| P001 | Imported profile current skills match independent dataset oracle | PASSED | JQA001 |
| E001 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P002 | Imported profile current skills match independent dataset oracle | PASSED | JQA002 |
| E002 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P003 | Imported profile current skills match independent dataset oracle | PASSED | JQA003 |
| E003 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P004 | Imported profile current skills match independent dataset oracle | PASSED | JQA004 |
| E004 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P005 | Imported profile current skills match independent dataset oracle | PASSED | JQA005 |
| E005 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P006 | Imported profile current skills match independent dataset oracle | PASSED | JQA006 |
| E006 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P007 | Imported profile current skills match independent dataset oracle | PASSED | JQA007 |
| E007 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P008 | Imported profile current skills match independent dataset oracle | PASSED | JQA008 |
| E008 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P009 | Imported profile current skills match independent dataset oracle | PASSED | JQA009 |
| E009 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P010 | Imported profile current skills match independent dataset oracle | PASSED | JQA010 |
| E010 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P011 | Imported profile current skills match independent dataset oracle | PASSED | JQA011 |
| E011 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P012 | Imported profile current skills match independent dataset oracle | PASSED | JQA012 |
| E012 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P013 | Imported profile current skills match independent dataset oracle | PASSED | JQA013 |
| E013 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P014 | Imported profile current skills match independent dataset oracle | PASSED | JQA014 |
| E014 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P015 | Imported profile current skills match independent dataset oracle | PASSED | JQA015 |
| E015 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P016 | Imported profile current skills match independent dataset oracle | PASSED | JQA016 |
| E016 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P017 | Imported profile current skills match independent dataset oracle | PASSED | JQA017 |
| E017 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P018 | Imported profile current skills match independent dataset oracle | PASSED | JQA018 |
| E018 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P019 | Imported profile current skills match independent dataset oracle | PASSED | JQA019 |
| E019 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P020 | Imported profile current skills match independent dataset oracle | PASSED | JQA020 |
| E020 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P021 | Imported profile current skills match independent dataset oracle | PASSED | JQA021 |
| E021 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P022 | Imported profile current skills match independent dataset oracle | PASSED | JQA022 |
| E022 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P023 | Imported profile current skills match independent dataset oracle | PASSED | JQA023 |
| E023 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| P024 | Imported profile current skills match independent dataset oracle | PASSED | JQA024 |
| E024 | All candidate eligibility and gains satisfy original catalog | PASSED | [] |
| B01 | Completed EV_006 excluded; EV_007 remains | PASSED | See contexts/profiles in evidence.json |
| B02 | Cap 3 course excluded for sole design 3-to-4 gap | PASSED | See contexts/profiles in evidence.json |
| B03 | Missing design prerequisite excludes EV_006 and EV_007 | PASSED | See contexts/profiles in evidence.json |
| B04 | Frontend-only events excluded for backend career switch | PASSED | See contexts/profiles in evidence.json |
| B05 | Junior cannot access advanced Middle design | PASSED | See contexts/profiles in evidence.json |
| B06 | No valid activity returns empty candidate catalog | PASSED | See contexts/profiles in evidence.json |
| B07 | Recurring completed speaking club remains eligible | PASSED | See contexts/profiles in evidence.json |
| B08 | No goal defaults to next grade without inventing explicit goal | PASSED | See contexts/profiles in evidence.json |
| B09 | Maximum grade with all skills 5 has no fabricated next grade | PASSED | See contexts/profiles in evidence.json |
| B10 | After review activity adds both capped gains | PASSED | See contexts/profiles in evidence.json |
| B11 | Before review no double gain | PASSED | See contexts/profiles in evidence.json |
| B12 | Skill above cap never decreases | PASSED | See contexts/profiles in evidence.json |
| B13 | Self-paced empty upcoming sessions eligible | PASSED | See contexts/profiles in evidence.json |
| B14 | Multi-skill cap preserves 5 while allowing cloud gain | PASSED | See contexts/profiles in evidence.json |
| B15 | Same-day review interpretation | NOT VERIFIED | Observed design level 2; README says after review but lacks intraday ordering. Strict > is defensible, cannot prove whether same-day completion was assessed. |
| C01 | History pair equal role/grade/skills/goal | PASSED | Only identity and history differ |
| C02 | Career goal changes target analysis and candidate pool | PASSED | Pair B |
| C03 | Completed event changes eligible alternatives | PASSED | Pair C |
| C04 | Grade changes eligible alternatives | PASSED | Pair E |
| C05 | Critical flags alone under modified target requirements | PASSED | Completed in supplementary isolated-catalog pair Z03-Z06; only critical flags differ. |
| S01 | unknown employee | PASSED | 404 |
| S02 | anonymous profile | PASSED | 401 |
| S03 | Employee cannot read another employee or HR | PASSED | /api/hr/dashboard: 403 |
| S04 | Employee cannot read another employee or HR | PASSED | /api/employees/JQA002: 403 |
| S05 | Employee cannot read another employee or HR | PASSED | /api/employees/JQA002/recommendations/context: 403 |
| S06 | Employee list includes only self | PASSED |  |
| S07 | Employee cannot import | PASSED | 403 |
| V01 | Unknown skill rejected on public import | PASSED | 422 |
| V02 | Malformed JSON rejected | PASSED | 422 |
| V03 | Duplicate history ID in upload rejected | PASSED | 422 |
| H01 | HR finds employee with no candidates | PASSED |  |
| H02 | HR reports employees without actual recommendation | FAILED | {'recommendation_status': 'not_implemented', 'employees_without_recommendation': None} |
| H03 | HR identifies specific employee with uncovered critical gap despite optional candidate | FAILED | JQA022 has unfillable critical design gap and optional speaking; only aggregate gaps are exposed |
| H04 | HR gap aggregation matches independent requirements | PASSED | 224 employees; source projections checked separately |
| H05 | HR participation counts match original plus imported history | PASSED |  |
| L001 | Public recommendation JQA001 | PASSED | 200 success |
| L002 | Public recommendation JQA002 | PASSED | 200 success |
| L003 | Public recommendation JQA003 | PASSED | 200 success |
| L004 | Public recommendation JQA004 | FAILED | 503 {'code': 'unavailable', 'message': 'Ответ AI не прошёл проверку фактов. Рекомендации не сохранены.', 'details': [{'reason': 'ai_unsupported_evidence'}]} |
| L005 | Public recommendation JQA005 | PASSED | 200 success |
| L006 | Public recommendation JQA006 | PASSED | 200 success |
| L007 | Public recommendation JQA007 | PASSED | 200 success |
| L008 | Public recommendation JQA008 | PASSED | 200 success |
| L009 | Public recommendation JQA009 | PASSED | 200 no_candidates |
| L010 | Public recommendation JQA010 | PASSED | 200 no_candidates |
| L011 | Public recommendation JQA011 | PASSED | 200 success |
| L012 | Public recommendation JQA012 | PASSED | 200 success |
| L013 | Public recommendation JQA013 | PASSED | 200 success |
| L014 | Public recommendation JQA014 | PASSED | 200 no_candidates |
| L015 | Public recommendation JQA015 | PASSED | 200 no_candidates |
| L019 | Public recommendation JQA019 | PASSED | 200 success |
| L020 | Public recommendation JQA020 | PASSED | 200 success |
| L021 | Public recommendation JQA021 | PASSED | 200 success |
| L022 | Public recommendation JQA022 | PASSED | 200 success |
| L024 | Public recommendation JQA024 | PASSED | 200 success |
| M01 | Critical design wins over lower/larger public-speaking gap | PASSED | ['EV_006'] |
| M04 | Critical design wins over lower/larger public-speaking gap | NOT VERIFIED | Initial JQA004 returned 503, so initial selection was unavailable. Independent controlled pair Z03/Z06 subsequently demonstrated critical sensitivity. |
| R01 | Repeated recommendation succeeds and preserves result | PASSED | Cached repeat is not independent LLM reasoning |
| I03 | Imported employee completes eligible self-paced activity | PASSED | 200 |
| I04 | Same completion command is idempotent | PASSED |  |
| I05 | Second complete with fresh command rejected | PASSED | 409 |
| I06 | Trajectory improves after completion | PASSED |  |
| I07 | Recommendation after complete no longer suggests completed course | PASSED | {'status': 'no_candidates', 'employee_id': 'JQA019', 'recommendations': [], 'revision': 2, 'as_of_date': '2026-10-01', 'hypotheses': [], 'clarifying_questions': []} |
| X01 | Reject fabricated EV_FAKE | PASSED | 503 {'error': {'code': 'unavailable', 'message': 'AI recommendation unavailable or returned unsupported evidence', 'details': []}} |
| X02 | Reject fabricated EV_999 | PASSED | 503 {'error': {'code': 'unavailable', 'message': 'AI recommendation unavailable or returned unsupported evidence', 'details': []}} |
| X03 | Reject fabricated free-text facts/course | FAILED | 200 {'status': 'success', 'employee_id': 'JQA005', 'recommendations': [{'event_id': 'EV_006', 'explanation': 'You completed 99 workshops because your manager forced you. This activity raises System Design to 99. Your goal is CEO. Take the invented Galactic Leadership Course.', 'evidence': [{'kind': 'current_grade', 'values': {'role': 'Backend Engineer', 'grade': 'Middle'}, 'source_ids': ['JQA005']}, {'kind': 'skill_levels', 'values': {'role': 'Backend Engineer', 'grade': 'Senior', 'skill_id': 'SK_API_DESIGN', 'current': 5, 'required': 4}, 'source_ids': ['SK_API_DESIGN']}, {'kind': 'attainable_gain', 'values': {'skill_id': 'SK_API_DESIGN', 'gain': 0}, 'source_ids': ['EV_006', 'SK_API_DESIGN']}], 'confidence': 'high', 'additional_value': None |
| T01 | Profile/API responses below 2 seconds | PASSED | {'profile': {'n': 24, 'min': 0.0018894000095315278, 'avg': 0.002790954165296474, 'p95': 0.004595500009600073, 'max': 0.0053168999729678035}, 'trajectory': {'n': 24, 'min': 0.0041456000180915, 'avg': 0.006167033325861364, 'p95': 0.007731200021225959, 'max': 0.007918899995274842}, 'hr': {'n': 1, 'min': 0.9681025000172667, 'avg': 0.9681025000172667, 'p95': 0.9681025000172667, 'max': 0.9681025000172667}, 'live_ai': {'n': 16, 'min': 2.750526699994225, 'avg': 4.183636412497435, 'p95': 5.976343399961479, 'max': 5.976343399961479}, 'recommendation_cached': {'n': 1, 'min': 0.005903100012801588, 'avg': 0.005903100012801588, 'p95': 0.005903100012801588, 'max': 0.005903100012801588}} |
| T02 | Live AI response below 10 seconds | PASSED | {'n': 16, 'min': 2.750526699994225, 'avg': 4.183636412497435, 'p95': 5.976343399961479, 'max': 5.976343399961479} |
| T03 | Browser rendered UI latency and full UI import click path | NOT VERIFIED | ASGI public API exercised; no browser automation |
| Z01 | Attractive activity excluded when mandatory | PASSED | ['mandatory'] |
| Z02 | Attractive activity excluded when no_sessions | PASSED | ['unavailable'] |
| Z03 | Critical-flag contrastive live recommendation False | PASSED | {'status': 'success', 'employee_id': 'JQA004', 'recommendations': [{'event_id': 'EV_006', 'explanation': "Given the employee's gap of 1 level in the critical skill System Design for their target Senior grade, and the event's offering to improve this skill from level 3 to 4, this offline 12-hour workshop is the most directly relevant development opportunity. The employee already meets or exceeds requirements in other key skills, making this focused enhancement of System Design crucial. The workshop also covers related skills like API Design and Observability, but the main value is the System Design upgrade needed for promotion readiness. Other options like the Architecture Review Circle also improve System Design but are less comprehensive a |
| Z04 | Critical-flag contrastive live recommendation True | PASSED | {'status': 'success', 'employee_id': 'JQA004', 'recommendations': [{'event_id': 'EV_036', 'explanation': "The employee's only notable skill gap relative to the Senior Backend Engineer benchmark is Public Speaking, a critical skill for that career goal. The Public Speaking Club event directly addresses this gap, providing an opportunity to develop this currently absent but required skill. It is more relevant now than architecture or system design events because the employee already meets or exceeds all other current and next-level requirements except Public Speaking, and this event’s short duration and frequent sessions facilitate timely skill development.", 'evidence': [{'kind': 'skill_levels', 'values': {'role': 'Backend Engineer', 'grade' |
| Z05 | Critical flags propagate independently of skill/role/grade/history | PASSED | Only Senior Backend critical_skills modified in temporary catalog; immutable source intact |
| Z06 | LLM selection responds to critical flag alone | PASSED | ['EV_006'] -> ['EV_036'] |
| Z07 | Imported identity has documented manual provisioning path | PASSED | README line 231 documents DEV_IDENTITIES_JSON before startup. Foreign/HR complete 403 is correct. Main I03-I07 confirm provisioned own employee completes and progresses. Automatic provisioning not required by source TЗ. |
| Z08 | Incomplete in_progress does not increase skills | PASSED | 200 |
| Z09 | Incomplete dropped does not increase skills | PASSED | 200 |
| Z10 | Incomplete overdue does not increase skills | PASSED | 200 |
| Z11 | Unknown registered status rejected (not in original schema) | PASSED | 422 |
| Z12 | Inconsistent completed percentage rejected | PASSED | 422 |
| Z13 | Malformed completion command rejected | PASSED | 422 |
| SEC08 | Public demo HR credential does not grant privileged data | FAILED | Public login/source credential demo-hr returned 200; UI exposes HR role button |
| PERF5 | Fresh recommendation API response under 10 seconds | PASSED | 9.910036 seconds, HTTP 200 |
| PERF12 | Fresh recommendation API response under 10 seconds | PASSED | 7.159150 seconds, HTTP 200 |
| PERF24 | Fresh recommendation API response under 10 seconds | PASSED | 3.851938 seconds, HTTP 200 |
| Q001 | Manual factual review: main JQA001 | FAILED | Claims Observability advances although current 5 exceeds event cap 4. |
| Q002 | Manual factual review: main JQA002 | PASSED | Correct critical System Design 3 to 4, role/goal, date/duration; subjective preference not treated as fact. |
| Q003 | Manual factual review: main JQA003 | PASSED | Correct critical gap and repeated club noncompletion; same ranking as positive history pair is justified. |
| Q005 | Manual factual review: main JQA005 | FAILED | Claims workshop enhances Observability although attainable gain is 0. |
| Q006 | Manual factual review: main JQA006 | PASSED | Correct completed EV_006, remaining EV_007, System Design 3 to 4. Communication gain described ambiguously as minimal, not an explicit numeric overclaim. |
| Q007 | Manual factual review: main JQA007 | PASSED | Correct critical gap, EV_006 and equal attainable System Design gain for EV_007. |
| Q008 | Manual factual review: main JQA008 | FAILED | Promises minor API Design gain despite current 5 and EV_005 cap 3. |
| Q011 | Manual factual review: main JQA011 | FAILED | Says EV_007 has no System Design gain; catalog/context show +1 and current 3. |
| Q012 | Manual factual review: main JQA012 | FAILED | Calls Data Modeling a critical skill; Senior Data Analyst critical set is Statistics and A/B Testing. |
| Q013 | Manual factual review: main JQA013 | FAILED | No career goal set, but explanation calls employee aiming for Senior; default assumption is not disclosed. |
| Q019 | Manual factual review: main JQA019 | FAILED | Calls Python a critical skill for Senior Backend; critical set is System Design and API Design. |
| Q020 | Manual factual review: main JQA020 | PASSED | Correct design gap and expressly no projected Observability gain; past club no-show followed by completion is not treated as current workshop failure. |
| Q021 | Manual factual review: main JQA021 | FAILED | Describes System Design and Communication as already expert while System Design is 3 and target 4. |
| Q022 | Manual factual review: main JQA022 | FAILED | Says critical backend skills are expert; System Design remains 3 versus 4 with no available closing activity. Hides the catalog gap. |
| Q024 | Manual factual review: main JQA024 | PASSED | Correct Cloud 2 to 3 and no redundant CI/CD gain at 5. |
| QS0 | Manual factual review: supplement critical_False | PASSED | Correct prioritization of critical design gap over public speaking; speculative interests explicitly need confirmation. |
| QS1 | Manual factual review: supplement critical_True | FAILED | Correctly switches to EV_036 but falsely says all other next-grade requirements met; System Design remains 3 vs 4. |
| QP5 | Manual factual review: performance JQA005 | PASSED | Correct critical design gap, gain, prerequisites and scheduling. |
| QP12 | Manual factual review: performance JQA012 | PASSED | Correct Data Modeling gap 2 and goal relevance; does not call it critical in this run. |
| QP24 | Manual factual review: performance JQA024 | PASSED | Correct sole Cloud gap and event eligibility. Speculative certification motivation explicitly flagged needs_confirmation. |
| MFH | Live history contrast changes explanation with defensible identical choice | PASSED | JQA002/JQA003 both EV_006; negative-history explanation explicitly deprioritizes club after declines/no_shows. |
| MFG | Explicit career switch overrides next-grade critical-only shortcut | PASSED | JQA011 EV_006 -> JQA012 EV_025 despite backend critical design gap remaining. Text has separately reported factual error. |

## Passed

Original source integrity; public new-profile/history import and identical reimport; 24 independent current-skill projections; all 24 candidate eligibility/gain sets; capped growth/no regression; review-before/after; prerequisites, role/grade and mandatory exclusions; self-paced availability; completed nonrepeatable exclusion and recurring exception; unknown/malformed inputs; duplicate history rejection; 403 for foreign employee/HR mutation and 401 for unauthenticated access; employee list privacy; HR aggregate counts; complete idempotency and trajectory refresh. Fake unknown IDs EV_FAKE and EV_999 are rejected. Candidate-free profiles return `no_candidates` without invented events.

Live contrastive evidence demonstrates history-aware explanation, career-goal-sensitive selection, completion-aware alternatives, grade-aware availability, and critical-flag-sensitive choice. The latter changes EV_006 to EV_036 when only the critical set changes. Deterministic calculations are considerably stronger than the prose explanations.

## Failed

15 failed assertions/reviews map to the six defects below. Ten of 20 successful real recommendation explanations failed this adversarial factual/assumption review. This rate describes the engineered sample only. Successful repeat samples for JQA005/JQA012 did not repeat their earlier hallucinations, confirming variable output rather than erasing the original failures. All returned real event IDs were eligible; failure is often in the explanation of a sensible choice.

## Critical defects

None confirmed. No fabricated event ID bypass, deterministic over-cap growth, broken public import or unauthorized access using an ordinary employee token was observed. This is not a production security certification.

## High defects

**D01 — Free-text explanation can contradict validated facts (HIGH).**

- Input: JQA001/005 with Observability 5, EV_006 cap 4; JQA008 API Design 5, EV_005 cap 3; JQA011 with EV_007 attainable design +1; JQA012/Data Analyst and JQA019/Backend target critical sets. Also Q021/Q022/QS1.
- Expected: no claimed positive gain at/above cap; exact catalog critical flags and remaining gaps; prose consistent with evidence.
- Actual: real outputs claim Observability/API gain despite 0, deny EV_007 design gain, label noncritical Data Modeling/Python critical, or say unmet requirements are already met. Q022 hides an unfillable critical gap. Local red-team injection with an eligible ID plus legitimate evidence also accepts level 99, 99 invented workshops, CEO goal and an invented course in prose (HTTP 200).
- How to reproduce: run suite, inspect `evidence.json.live_results` for the named profiles and `injections.prose`; manual reviews Q001/Q005/Q008/Q011/Q012/Q019/Q021/Q022/QS1 and X03. Fake injection is deterministic validation-boundary proof; actual live responses independently prove real hallucinations.
- Related requirement: skill gain/max_level, factual explainability, no invented events/goals/history, no hidden gaps. Structured evidence is checked; arbitrary prose semantics are not.

**D03 — HR cannot see who actually lacks a recommendation (HIGH).**

- Input: imported profiles, including valid candidates, then `GET /api/hr/dashboard`.
- Expected: discoverable employees with no recommendation or failed generation.
- Actual: `recommendation_status="not_implemented"`, `employees_without_recommendation=null`. `employees_without_candidate` is a different concept and misses a candidate-bearing employee whose LLM failed.
- How to reproduce: H02; inspect `evidence.json.hr` and `backend/app/services/hr.py` response construction.
- Related requirement: HR visibility into employees falling out of development and stage 11 employees without recommendations.

**D04 — HR misses partial critical catalog gaps (HIGH).**

- Input: JQA022 has System Design 3/4 critical; EV_006/007 completed before review, EV_005 capped at 3. Public Speaking 1/2 remains eligible through EV_036.
- Expected: HR can identify this employee's unfillable critical design gap even while an optional activity is available.
- Actual: JQA022 is absent from employees_without_candidate; dashboard exposes only aggregate skill counts, without per-employee critical catalog coverage. Live recommendation additionally claims critical backend skills are expert (D01).
- How to reproduce: H03, Q022; compare JQA014 (no candidates, correctly found) with JQA022 (one optional candidate, missing from catalog-gap discovery).
- Related requirement: stages 2/11; employees whose critical gaps cannot be covered must be discoverable by HR.

**D06 — Valid adversarial request can end with no usable recommendation (HIGH).**

- Input: JQA004, design critical gap 1 vs public speaking noncritical gap 2, with eligible candidates.
- Expected: 1-3 usable evidence-based recommendations or an intelligible clarification.
- Actual: initial HTTP 503 `ai_unsupported_evidence`; 1 of 21 provider calls failed. The later independently defined critical-pair baseline succeeds; reliability remains unproven.
- How to reproduce: recorded `evidence.json.live_results.JQA004`, L004. New live runs are stochastic; the exact failure is not guaranteed to recur. No unsupported answer was served, which is a sound guard, but the employee scenario still failed.
- Related requirement: core recommendation must work for unknown adversarial profiles. Invalid-output handling is safe but lacks a usable result in this sample.

## Medium defects

**D02 — Default trajectory presented as employee intent (MEDIUM).**

- Input: JQA013 `career_goal=null`.
- Expected: clearly disclose next-grade trajectory as a default assumption; do not imply stated ambition.
- Actual: live explanation says employee is "aiming for Senior level" without disclosing default. API trajectory correctly retains career_goal_analysis=null.
- How to reproduce: Q013 in saved live evidence; new live wording may vary.
- Related requirement: no-career-goal case and prohibition on invented career goals.

**D05 — Demo identities do not establish a private employee/HR trust boundary (MEDIUM, documented MVP limitation).**

- Input: public login/source token `demo-hr`, accessible from the HR login button, sent to dashboard endpoint.
- Expected: a person without HR authorization cannot self-select HR and read engagement data.
- Actual: HTTP 200 HR aggregates with publicly supplied HR token. Employee-token access checks themselves pass.
- How to reproduce: SEC08; `frontend/src/components/connected-career-app.tsx` public HR option and `GET /api/hr/dashboard` using demo credential.
- Related requirement: privacy and employee/HR separation. README explicitly labels these local-demo tokens and excludes production authentication; loopback binding reduces exposure. This is a known scope limitation for the judging discussion, not a hidden token leak or evidence that a foreign employee bearer token bypasses authorization.

## Low defects

None separately counted. Installed Starlette emits an httpx deprecation warning; it did not invalidate test execution. Clarifying questions in one English-profile response were Russian, an optional localization inconsistency noted without inflating mandatory-case severity totals.

## Multi-factor recommendation tests

All 20 successful model responses had a concrete eligible activity and at least three distinct evidence kinds. Coverage by category:

| Factor | Independent evidence | Result |
|---|---|---|
| Current role/grade | 24 API candidate checks; grade pair | PASS |
| Target role/grade | Career pair EV_006 to EV_025 | PASS |
| Skill gaps | Correct numerical context/projection oracle | PASS deterministic; prose failures D01 |
| Critical skills | Critical-only controlled pair EV_006 to EV_036 | PASS sensitivity; prose flags sometimes false |
| Activity history | Same profile positive/negative club outcomes affect explanation; completed EV_006 removed | PASS on sampled cases |
| Eligibility | Independent catalog role/grade/mandatory/availability checks | PASS |
| Expected gain | Independent exact candidate gain oracle | PASS deterministic; real prose overclaims |
| max_level | At cap / above cap / multi-skill capped gains | PASS deterministic; D01 prose fails |
| Prerequisites | Design level 1 excludes advanced design events; EV_005 remains | PASS |

The observed engine cannot be accurately characterized as only lowest skill, largest gap, first eligible ID or critical-only ranking. Career-goal and critical-only perturbations alter selection, and history affects explanation. This is bounded behavioral evidence, not proof that all possible profiles receive optimal recommendations. Explanations sometimes invent comparative benefits for tied candidates; their equal numeric gain is known, but catalog descriptions leave room for subjective preference. No unjustified failure is assigned solely because a tie selected EV_006 instead of EV_007.

## Contrastive tests

| Pair | Only meaningful input difference | Output difference |
|---|---|---|
| A JQA002 / JQA003 | History: completed club vs repeated no_show/declined, all before review | Both EV_006; negative-history explanation explicitly excludes club on participation concerns. Same critical gap justifies same choice. |
| B JQA011 / JQA012 | Career goal Backend Senior vs Data Analyst Senior | EV_006 to EV_025; own role remains Backend. Shows explicit goal matters even with remaining next-grade critical design gap. |
| C JQA005 / JQA006 | EV_006 completed before review | EV_006 to EV_007, same current skill snapshot. |
| D isolated JQA004 | Only Senior Backend critical set changes design to public speaking | EV_006 to EV_036; same requirements, employee, gaps, history and catalog. Prose of second response incorrectly hides remaining design gap. |
| E JQA005 / JQA010 | Current grade Middle to Junior | EV_006 to no_candidates; advanced design activities unavailable and fundamentals capped. |

Identity/record IDs necessarily differ across imported pair members; name, demographics and untested profile fields are held equal. Pair D reuses the exact employee across separate isolated catalogs. Full inputs/outputs preserved in evidence/supplement JSON. One initial JQA004 failure was not silently replaced by a later success.

## Import test

Public `POST /api/dataset/import` accepts the actual original JSON envelope and CSV schema, adds all 24 employees/41 rows, and reimport is idempotent. Imported employees are readable through standard profile/trajectory/recommendation APIs. JQA019 receives live EV_012, completes via self-token, Python moves 3 to 4, trajectory coverage improves, repeated identical command is idempotent, fresh duplicate returns 409, and subsequent recommendation becomes no_candidates. No source-code hardcoding is needed.

Authentication preparation is explicit: the harness preconfigured employee self-tokens to test completion. The unmodified configured HR and original employee identities correctly return 403 for a new jury employee's completion. README line 231 documents adding imported employee identities to DEV_IDENTITIES_JSON before Python startup; import itself does not issue credentials. This is an operational step for the defense, **not** an import failure. Browser click-through and automatic token issuance are not claimed.

## Skill recalculation tests

JQA017 review-minus-one-day: design stays 2. JQA018 review-plus-one-day: design 2 to 3 and API 2 to 3. JQA016 same calendar day: stays 2, consistent with strict-after reading; assessment/completion intraday order is not defined, marked NOT VERIFIED as an ambiguity rather than a fabricated rule. JQA023 skill above activity cap remains 5. JQA024 Cloud gain 1 while CI/CD gain 0. JQA019 completion projects correctly, changes trajectory and removes nonrepeatable course. In-progress/dropped/overdue rows grant no skill gain. Duplicate history and duplicate complete do not double-count.

## Explainability / hallucination tests

All 20 real recommendation explanations reviewed individually in Q* registry rows. **10 passed, 10 failed** factual/default-assumption review. Primary ranking can be correct while its justification is false. Strongest actual examples: "advances Observability" at skill 5/cap 4; "minor [API Design] gain" at 5/cap 3; EV_007 described as offering no design gain though its verified gain is 1; noncritical Python/Data Modeling called critical; still-deficient design described as expert/met.

Fake provider tests are separate: EV_FAKE/EV_999 -> 503 rejection. An eligible event with valid evidence and absurd prose -> 200. This establishes the backend only validates structured evidence/ID membership, not that explanation text agrees. No assertion that real OpenAI returned EV_FAKE, level 99 or the invented Galactic course is made. Real source/history are complete in preserved context; no imagined reasons for missed/declined were observed in successful live outputs. Hypotheses marked needs_confirmation are distinguished from asserted facts.

## Performance

| Measurement | n | min s | avg s | p95 s | max s |
|---|---:|---:|---:|---:|---:|
| profile | 24 | 0.001889 | 0.002791 | 0.004596 | 0.005317 |
| trajectory | 24 | 0.004146 | 0.006167 | 0.007731 | 0.007919 |
| hr | 1 | 0.968103 | 0.968103 | 0.968103 | 0.968103 |
| live_ai | 16 | 2.750527 | 4.183636 | 5.976343 | 5.976343 |
| recommendation_cached | 1 | 0.005903 | 0.005903 | 0.005903 | 0.005903 |
| recommendation_api_5_samples | 5 | 3.851938 | 6.537025 | 9.910036 | 9.910036 |
| recommendation_api_3_sequential | 3 | 3.851938 | 6.973708 | 9.910036 | 9.910036 |

Times are wall-clock seconds; p95 is nearest rank ceil(0.95*n), not interpolation. `live_ai` is **provider adapter refine timing for the first 16 actual calls**, including its one rejected output; it excludes surrounding API/context/persistence work. `recommendation_api_3_sequential` is three fresh sequential public POST requests, including all ASGI/business/persistence work. `recommendation_api_5_samples` combines those three with two isolated critical-pair POSTs. Cache repeat is not a model latency sample. All five measured fresh API calls meet 10 s on this host, but maximum **9.910 s** leaves little margin. Profiles/trajectory samples meet 2 s. HR has only one timed observation, so its p95 is just that observation.

Total live calls across all phases **21**, errors **1** (ai_unsupported_evidence), no unbounded repeats, no automatic provider retries. Four candidate-free main responses and post-complete no_candidates invoke no LLM. Initial raw successful recommendations are 15; supplemental 2; performance 3. Live timings are not presented as browser end-to-end or concurrent-load measurements.

Source inspection shows raw source files loaded into the dataset snapshot at application startup; profile reads use in-memory repositories, not an obvious N+1 disk/network query loop. HR traverses employees and trajectories; notification generation/commit rebuilds dataset snapshots. At 224 employees measured latency is acceptable, but larger data, concurrent workers, browser rendering and network/proxy delay remain unverified. No benchmark-scale claim is made.

## HR view

Independent aggregation against role requirements matches all skill-gap counts for 224 profiles. Participation counters match original plus imported CSV rows. JQA014 is found as no-candidate; JQA022's partial critical gap is not identified. Actual no-recommendation status is unimplemented. Employee bearer token cannot access HR dashboard or another employee/context, and its employee list includes only self. Public demo HR role remains the documented authentication limitation D05.

## Jury-risk scenarios

1. A correct chosen event is defended with a false capped gain or critical flag; jury compares against dataset and rejects explainability (D01).
2. Employee has an unfillable critical gap plus a soft-skill option; recommendation implies readiness and HR fails to flag the catalog issue (D01/D04).
3. A valid unknown profile produces ai_unsupported_evidence and no recommendation during a one-shot demonstration (D06).
4. HR cannot distinguish users with candidates but failed/missing AI recommendations (D03).
5. Public demo HR credentials do not demonstrate an actual private user boundary (D05). Also prepare documented own employee tokens for imported IDs before demonstrating complete; otherwise 403 is expected.

## Final assessment

The system accepts unknown adversarial profiles and provides genuine sampled multi-factor selection. Deterministic eligibility, growth, projection and completion survived these checks. **It is not yet reliable enough to promise three unknown jury profiles will all yield a factually correct explanation.** Half of this intentionally difficult successful-output sample contained false facts or an undisclosed career assumption, one provider output was rejected, and HR visibility has concrete gaps.

TOTAL TESTS: **160**  
PASSED: **142**  
FAILED: **15**  
NOT VERIFIED: **3**  
CRITICAL: **0**  
HIGH: **4**  
MEDIUM: **2**  
LOW: **0**

Severity totals count unique defects D01-D06; failed totals count assertions/reviews. Three explicit NOT VERIFIED rows: same-day intraday assessment interpretation, original JQA004 ranking when its response failed, and browser-rendered import/latency. Longer-term model reliability and deployment/concurrent scale are additional scope limitations, not secretly counted passing tests. No production fixes were made. Stop here for review.
