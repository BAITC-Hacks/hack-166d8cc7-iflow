import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.ai.recommender import validate_recommendation_result
from app.core.config import Settings
from app.main import create_app
from app.repositories.dataset import build_snapshot, parse_employees
from app.repositories.history import parse_history
from app.schemas.recommendation import RecommendationResult, RecommendationItem
from app.services.recommendation_context import build_recommendation_context
from app.services.hr import build_hr_dashboard

FIX = Path(__file__).resolve().parents[2] / 'tests/fixtures/jury_profiles'


@pytest.fixture(scope='module')
def jury(real_bundle):
    profiles = parse_employees((FIX/'employees.json').read_bytes()).employees
    history = parse_history((FIX/'activity_history.csv').read_bytes())
    return build_snapshot(real_bundle.model_copy(update={
        'employees': real_bundle.employees + tuple(profiles),
        'history': real_bundle.history + tuple(history)}))


@pytest.mark.parametrize('employee_id', [f'JQA{i:03}' for i in range(1,25)])
def test_jury_prose_is_grounded_even_with_fabricated_ai_claims(jury, clock, employee_id):
    context = build_recommendation_context(employee_id, jury, clock)
    for candidate in context.candidates:
        poisoned = RecommendationResult(status='success', employee_id=employee_id, revision=context.revision,
            as_of_date=clock, recommendations=[RecommendationItem(event_id=candidate.event_id,
            explanation='Galactic course raises skill to 99. Employee wants to be CEO.', evidence=candidate.factors)])
        result = validate_recommendation_result(context, poisoned)
        assert 'Galactic' not in result.model_dump_json() and 'CEO' not in result.model_dump_json()
        if result.recommendations:
            text = result.recommendations[0].explanation
            event = jury.events.get(candidate.event_id)
            for gain in event.develops_skills:
                actual = max(0, min(context.current_skills.get(gain.skill_id,0)+gain.gain,gain.max_level)-context.current_skills.get(gain.skill_id,0))
                assert f'actual gain +{actual}, activity cap {gain.max_level}' in text
            if context.employee.career_goal is None:
                assert 'not a stated employee ambition' in text
        assert validate_recommendation_result(context,result) == result


def test_hr_partial_catalog_gap_and_real_generation_states(jury, clock):
    result = build_hr_dashboard(jury,clock,{'JQA001':'ready','JQA004':'failed','JQA005':'stale'})
    assert 'JQA001' not in result.employees_without_recommendation
    assert {'JQA004','JQA005'} <= set(result.employees_without_recommendation)
    gap = next(g for g in result.critical_catalog_gaps if g['employee_id']=='JQA022' and g['skill_id']=='SK_SYSTEM_DESIGN')
    assert gap['attainable_level']==3 and gap['required_level']==4
    assert 'JQA022' not in result.employees_without_candidate


def test_env_startup_rejects_public_demo_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv('DEV_IDENTITIES_JSON',raising=False)
    path=tmp_path/'.env'
    path.write_text('DEV_IDENTITIES_JSON=\'{"demo-hr":{"role":"hr"},"private-test":{"role":"hr"}}\'')
    settings=Settings.from_env(path).model_copy(update={'state_path':tmp_path/'state.json','notifications_worker_enabled':False})
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/hr/dashboard',headers={'Authorization':'Bearer demo-hr'}).status_code==401
        assert client.get('/api/hr/dashboard',headers={'Authorization':'Bearer private-test'}).status_code==200
    assert Settings().dev_identities == {}


def test_provisioning_preserves_keys_and_existing_private_identity(tmp_path):
    from provision_access import provision
    from dotenv import dotenv_values
    path=tmp_path/'.env'
    path.write_text('OPENAI_API_KEY=private-api\nDEV_IDENTITIES_JSON=\'{"demo-hr":{"role":"hr"}}\'\n')
    assert provision(path,['E0004'],hr=True)==2
    first=dotenv_values(path,encoding='utf-8-sig')
    assert first['OPENAI_API_KEY']=='private-api'
    assert provision(path,['E0004'],hr=True)==2
    assert dotenv_values(path,encoding='utf-8-sig')==first
    assert all(len(key)>=32 for key in json.loads(first['DEV_IDENTITIES_JSON']))
