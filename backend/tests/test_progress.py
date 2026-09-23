from datetime import date
import pytest
from app.schemas.activity import SkillGain

def test_gain_does_not_reduce_skill():
    from app.services.progress_engine import apply_gains
    assert apply_gains({"SK_PYTHON":4},[SkillGain(skill_id="SK_PYTHON",gain=1,max_level=3)]) == {"SK_PYTHON":4}

@pytest.mark.parametrize("day,expected",[("2026-08-31",1),("2026-09-01",1),("2026-09-02",2),("2026-10-02",1)])
def test_assessment_and_snapshot_boundaries(day,expected,make_employee,events,clock):
    from app.services.progress_engine import project_skills
    from app.schemas.history import EffectiveCompletion
    c=EffectiveCompletion(completion_key="r1",event_id="EV_012",completed_on=date.fromisoformat(day))
    assert project_skills(make_employee(),[c],events,clock)["SK_PYTHON"]==expected

@pytest.mark.parametrize("current,gain,cap,expected",[(0,1,3,1),(3,2,4,4),(5,1,3,5)])
def test_missing_skill_and_caps(current,gain,cap,expected):
    from app.services.progress_engine import apply_gains
    assert apply_gains({} if current==0 else {"SK_PYTHON":current},[SkillGain(skill_id="SK_PYTHON",gain=gain,max_level=cap)])["SK_PYTHON"]==expected

@pytest.mark.parametrize("status,pct",[("no_show",0),("declined",0),("dropped",20),("in_progress",40),("overdue",0)])
def test_noncompleted_statuses_do_not_contribute(status,pct,make_history):
    from app.services.progress_engine import historical_completions
    assert historical_completions([make_history(status=status,completion_pct=pct)]) == []

def test_duplicate_and_projection_does_not_mutate(make_employee,events,clock,make_history):
    from app.services.progress_engine import project_skills,historical_completions
    emp=make_employee(); c=historical_completions([make_history()])
    assert project_skills(emp,c+c,events,clock)["SK_PYTHON"]==2
    assert emp.skills=={"SK_PYTHON":1}

def test_chronological_projection(make_employee,make_event,clock):
    from app.repositories.events import EventRepository
    from app.schemas.history import EffectiveCompletion
    from app.services.progress_engine import project_skills
    a=make_event(event_id="a",develops_skills=[{"skill_id":"SK_PYTHON","gain":2,"max_level":2}])
    b=make_event(event_id="b",develops_skills=[{"skill_id":"SK_PYTHON","gain":1,"max_level":5}])
    cs=[EffectiveCompletion(completion_key="b",event_id="b",completed_on=date(2026,9,3)),EffectiveCompletion(completion_key="a",event_id="a",completed_on=date(2026,9,2))]
    assert project_skills(make_employee(),cs,EventRepository((a,b)),clock)["SK_PYTHON"]==3

def test_unknown_event_rejected(make_employee,events,clock):
    from app.schemas.history import EffectiveCompletion
    from app.services.progress_engine import project_skills
    with pytest.raises(ValueError):
        project_skills(make_employee(),[EffectiveCompletion(completion_key="a",event_id="unknown",completed_on=date(2026,9,2))],events,clock)
