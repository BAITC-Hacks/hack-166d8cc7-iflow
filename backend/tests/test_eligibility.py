from datetime import date
import pytest
from app.schemas.responses import TargetAnalysis,SkillGap
from app.services.progress_engine import participation_views

def evaluate(make_employee,make_event,**changes):
    from app.services.eligibility import evaluate_event
    args=dict(employee=make_employee(),current={"SK_PYTHON":1},
        targets=[TargetAnalysis(role="Backend Engineer",grade="Senior",gaps=[SkillGap(skill_id="SK_PYTHON",name="Python",current_level=1,required_level=4,gap=3,is_critical=True)],requirement_coverage=.25)],
        history=[],event=make_event(),as_of_date=date(2026,10,1),repeatable_event_ids=frozenset({"EV_036"}))
    args.update(changes)
    return evaluate_event(**args)

@pytest.mark.parametrize("changes,reason",[
    ({"mandatory":True},"mandatory"),({"target_roles":["Frontend Engineer"]},"audience_role"),
    ({"target_grades":["Lead"]},"audience_grade"),({"prerequisites":{"SK_PYTHON":3}},"prerequisites"),
    ({"develops_skills":[]},"no_target_gain"),({"format":"online","upcoming_sessions":[]},"unavailable")])
def test_rejection_reasons(changes,reason,make_employee,make_event):
    result=evaluate(make_employee,make_event,event=make_event(**changes))
    assert not result.eligibility.eligible and reason in result.eligibility.reasons

def test_self_paced_no_sessions_allowed(make_employee,make_event):
    assert evaluate(make_employee,make_event).eligibility.eligible

def test_scheduled_availability(make_employee,make_event):
    result=evaluate(make_employee,make_event,event=make_event(format="online",upcoming_sessions=["2026-09-01","2026-10-03"]))
    assert result.eligibility.eligible and result.eligibility.next_session==date(2026,10,3)

def test_completed_and_repeatable(make_employee,make_event,make_history):
    history=participation_views([make_history()])
    assert not evaluate(make_employee,make_event,history=history).eligibility.eligible
    assert evaluate(make_employee,make_event,history=history,repeatable_event_ids=frozenset({"EV_012"})).eligibility.eligible

def test_no_shows_are_facts_not_bans(make_employee,make_event,make_history):
    history=participation_views([make_history(status="no_show",completion_pct=0)])
    assert evaluate(make_employee,make_event,history=history).eligibility.eligible

def test_feature_bundle_preserves_all_evidence(make_employee,make_event,make_history):
    history=participation_views([make_history(record_id=str(i),status=s,completion_pct=p) for i,(s,p) in enumerate([("completed",100),("no_show",0),("declined",0),("dropped",10)])])
    result=evaluate(make_employee,make_event,history=history,repeatable_event_ids=frozenset({"EV_012"}))
    kinds={f.kind for f in result.factors}
    assert {"current_grade","target_grade","skill_levels","critical_skill","attainable_gain","completed_history","participation_outcomes","availability"} <= kinds
    outcomes=next(f for f in result.factors if f.kind=="participation_outcomes")
    assert outcomes.values=={"no_show":1,"declined":1,"dropped":1}
    assert set(outcomes.source_ids)=={"1","2","3"}
    assert result.possible_skill_gains=={"SK_PYTHON":1} and result.score is None
