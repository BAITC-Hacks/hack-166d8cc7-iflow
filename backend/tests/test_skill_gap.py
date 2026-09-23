import pytest
from app.schemas.skill import RoleProfile
from app.repositories.dataset import build_snapshot

@pytest.mark.parametrize("level,required,gap",[(5,4,0),(2,4,2),(0,3,3)])
def test_gaps(level,required,gap,skills):
    from app.services.skill_gap import calculate_gaps
    p=RoleProfile(role="Backend Engineer",grade="Senior",required_skills={"SK_PYTHON":required},critical_skills=["SK_PYTHON"])
    row=calculate_gaps({"SK_PYTHON":level} if level else {},p,skills)[0]
    assert (row.gap,row.is_critical)==(gap,True)

@pytest.mark.parametrize("grade,next_grade",[("Junior","Middle"),("Middle","Senior"),("Senior","Lead"),("Lead",None)])
def test_next_grade_order_and_lead(grade,next_grade,tiny_bundle,make_employee,clock):
    from app.services.trajectory import build_trajectory
    b=tiny_bundle.model_copy(update={"employees":(make_employee(grade=grade,career_goal=None),)})
    result=build_trajectory("TEST_EMP",build_snapshot(b),clock)
    assert result.next_grade==next_grade
    if grade=="Lead":
        assert result.requirement_coverage is None and result.next_grade_gaps==[]

def test_cross_role_goal_stays_separate(tiny_bundle,make_employee,clock):
    from app.services.trajectory import build_trajectory
    b=tiny_bundle.model_copy(update={"employees":(make_employee(career_goal={"target_role":"Frontend Engineer","target_grade":"Senior"}),)})
    result=build_trajectory("TEST_EMP",build_snapshot(b),clock)
    assert result.next_grade=="Senior"
    assert result.career_goal_analysis.role=="Frontend Engineer"

@pytest.mark.parametrize("required,current,expected",[({"SK_PYTHON":4,"SK_SQL":2},{"SK_PYTHON":5,"SK_SQL":1},5/6),({},{},1)])
def test_coverage(required,current,expected,skills):
    from app.services.skill_gap import analyze_target
    p=RoleProfile(role="Backend Engineer",grade="Senior",required_skills=required,critical_skills=[])
    assert analyze_target(current,p,skills).requirement_coverage==pytest.approx(expected)

def test_unknown_employee(tiny_bundle,clock):
    from app.services.trajectory import build_trajectory
    with pytest.raises(LookupError):
        build_trajectory("missing",build_snapshot(tiny_bundle),clock)
