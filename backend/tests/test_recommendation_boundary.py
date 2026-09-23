import pytest
from app.repositories.dataset import build_snapshot
from app.services.trajectory import build_trajectory

def context_for(tiny_bundle,clock):
    from app.ai.client import AIRefinementInput
    from app.services.trajectory import targets_for
    from app.services.progress_engine import current_skills
    snap=build_snapshot(tiny_bundle)
    employee=snap.employees.get("TEST_EMP")
    targets=targets_for(employee,current_skills(snap,"TEST_EMP",clock),snap)
    return AIRefinementInput(employee_id="TEST_EMP",current_grade="Middle",targets=[t for t in targets if t],
        candidates=build_trajectory("TEST_EMP",snap,clock).candidates,revision=0,as_of_date=clock)

@pytest.mark.parametrize("case",["invented","duplicate","empty","four","two_factors","changed_fact","wrong_revision","false_no_candidates"])
def test_output_validation(case,tiny_bundle,clock):
    from app.ai.recommender import validate_recommendation_result
    from app.schemas.recommendation import RecommendationResult
    context=context_for(tiny_bundle,clock);candidate=context.candidates[0]
    evidence=[]
    for f in candidate.factors:
        if f.kind not in [x["kind"] for x in evidence]: evidence.append(f.model_dump(mode="json"))
    item={"event_id":candidate.event_id,"explanation":"Evidence backed test explanation","evidence":evidence}
    data={"status":"success","employee_id":"TEST_EMP","recommendations":[item],"revision":0,"as_of_date":str(clock)}
    if case=="invented": item["event_id"]="UNKNOWN"
    if case=="duplicate": data["recommendations"]=[item,item]
    if case=="empty": data["recommendations"]=[]
    if case=="four": data["recommendations"]=[item]*4
    if case=="two_factors": item["evidence"]=evidence[:2]
    if case=="changed_fact": item["evidence"][0]["values"]["grade"]="invented"
    if case=="wrong_revision": data["revision"]=4
    if case=="false_no_candidates": data.update(status="no_candidates",recommendations=[])
    with pytest.raises(ValueError): validate_recommendation_result(context,RecommendationResult.model_validate(data))

def test_supported_result_and_no_candidates(tiny_bundle,clock):
    from app.ai.recommender import validate_recommendation_result
    from app.schemas.recommendation import RecommendationResult,RecommendationItem
    context=context_for(tiny_bundle,clock);c=context.candidates[0]
    result=RecommendationResult(status="success",employee_id="TEST_EMP",recommendations=[RecommendationItem(event_id=c.event_id,explanation="Test explanation",evidence=c.factors)],revision=0,as_of_date=clock)
    assert validate_recommendation_result(context,result)==result
    empty=context.model_copy(update={"candidates":[]})
    none=RecommendationResult(status="no_candidates",employee_id="TEST_EMP",recommendations=[],revision=0,as_of_date=clock)
    assert validate_recommendation_result(empty,none)==none
