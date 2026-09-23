from uuid import uuid4
from app.repositories.dataset import build_snapshot
from app.repositories.state import StateRepository
from app.services.dataset import DatasetService
from app.core.auth import Principal
from app.schemas.responses import CompletionCommand

def dashboard(snapshot,clock):
    from app.services.hr import build_hr_dashboard
    return build_hr_dashboard(snapshot,clock)

def test_recommendation_coverage_is_unknown(tiny_bundle,clock):
    r=dashboard(build_snapshot(tiny_bundle),clock)
    assert r.recommendation_status=="not_implemented" and r.employees_without_recommendation is None

def test_gap_counts_count_employees_not_levels(tiny_bundle,make_employee,clock):
    b=tiny_bundle.model_copy(update={"employees":(make_employee(),make_employee(employee_id="SECOND",skills={"SK_PYTHON":3}))})
    r=dashboard(build_snapshot(b),clock)
    assert next(x.employee_count for x in r.skill_gap_counts if x.skill_id=="SK_PYTHON")==2

def test_lead_excluded_from_next_grade_gaps(tiny_bundle,make_employee,clock):
    b=tiny_bundle.model_copy(update={"employees":(make_employee(grade="Lead",career_goal=None),)})
    r=dashboard(build_snapshot(b),clock)
    assert r.skill_gap_counts==[] and r.employees_without_candidate==["TEST_EMP"]

def test_participation_transition_counted_once(tiny_bundle,make_history,tmp_path,clock):
    from app.services.completion import complete_activity
    b=tiny_bundle.model_copy(update={"history":(make_history(status="in_progress",completion_pct=40),)})
    ds=DatasetService(build_snapshot(b),StateRepository(tmp_path/"s.json"),"h")
    assert dashboard(ds.capture(),clock).participation_by_event[0].status_counts=={"in_progress":1}
    complete_activity(Principal(role="employee",employee_id="TEST_EMP"),"TEST_EMP","EV_012",CompletionCommand(command_id=uuid4(),source_record_id="TEST_REC"),ds,clock)
    assert dashboard(ds.capture(),clock).participation_by_event[0].status_counts=={"completed":1}

def test_real_hr_response_budget(real_bundle,clock):
    import time
    snapshot=build_snapshot(real_bundle)
    start=time.perf_counter()
    result=dashboard(snapshot,clock)
    elapsed=time.perf_counter()-start
    assert len(result.participation_by_event)==40
    assert elapsed<2.0, f'HR calculation took {elapsed:.2f}s (spec budget: 2s)'
