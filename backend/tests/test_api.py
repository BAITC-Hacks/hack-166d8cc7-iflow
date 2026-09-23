from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def api_settings(tmp_path):
    from app.core.config import Settings
    return Settings(raw_dir=Path(__file__).resolve().parents[2]/"data/raw",state_path=tmp_path/"state.json",
        dev_identities={"test-self":{"role":"employee","employee_id":"E0001"},"test-other":{"role":"employee","employee_id":"E0002"},"test-hr":{"role":"hr"}})

@pytest.fixture
def api_client(api_settings):
    from app.main import create_app
    with TestClient(create_app(api_settings)) as client:
        yield client

def auth(token="test-self"): return {"Authorization":"Bearer "+token}

def test_health_is_public(api_client):
    assert api_client.get("/health").json()=={"status":"ok"}

@pytest.mark.parametrize("headers",[{},auth("invalid")])
def test_missing_and_unknown_token_401(api_client,headers):
    assert api_client.get("/api/employees",headers=headers).status_code==401

def test_foreign_employee_forbidden(api_client):
    r=api_client.get("/api/employees/E0002",headers=auth())
    assert r.status_code==403 and r.json()["error"]["code"]=="forbidden"

def test_spoofed_role_ignored(api_client):
    assert api_client.get("/api/employees/E0002",headers={**auth(),"X-Role":"hr"}).status_code==403

def test_employee_list_contains_only_self(api_client):
    r=api_client.get("/api/employees",headers=auth())
    assert [x["employee_id"] for x in r.json()["items"]]==["E0001"]
    assert r.headers["cache-control"]=="no-store"

def test_hr_can_read_any_profile(api_client):
    assert api_client.get("/api/employees/E0002",headers=auth("test-hr")).status_code==200

def test_authorized_missing_employee_404(api_client):
    assert api_client.get("/api/employees/missing",headers=auth("test-hr")).status_code==404

def test_trajectory_contains_expected_contract(api_client):
    r=api_client.get("/api/employees/E0001/trajectory",headers=auth())
    assert r.status_code==200
    assert r.json()["next_grade"]=="Middle"
    assert r.json()["next_grade_gaps"]
    assert all(x["eligibility"]["eligible"] for x in r.json()["candidates"])
    p=api_client.get("/api/employees/E0001",headers=auth()).json()
    assert p["current_skills"]["SK_PYTHON"]>=p["profile"]["skills"]["SK_PYTHON"]

def test_errors_do_not_echo_token(api_client):
    r=api_client.get("/api/employees",headers=auth("sensitive-token"))
    assert "sensitive-token" not in r.text and "input" not in r.text

def test_earlier_application_date_rejected(api_settings):
    from app.main import create_app
    with pytest.raises(ValueError):
        with TestClient(create_app(api_settings.model_copy(update={"application_date":"2020-01-01"}))): pass

def test_bad_source_prevents_startup(api_settings,tmp_path):
    from app.main import create_app
    with pytest.raises((ValueError,FileNotFoundError)):
        with TestClient(create_app(api_settings.model_copy(update={"raw_dir":tmp_path}))): pass

def test_employee_cannot_import(api_client):
    assert api_client.post('/api/dataset/import',headers=auth()).status_code==403

def test_no_import_payload(api_client):
    assert api_client.post('/api/dataset/import',headers=auth('test-hr')).status_code==422

def test_upload_limit_chunked(api_client):
    response=api_client.post('/api/dataset/import',headers={**auth('test-hr'),'Content-Type':'multipart/form-data; boundary=test'},content=iter([b'x'*(1024*1024)]*11))
    assert response.status_code==413
    assert api_client.app.state.dataset.state.revision==0

def test_invalid_request_redacts_input(api_client):
    response=api_client.post('/api/employees/E0001/activities/EV_012/complete',headers=auth(),json={'command_id':'sensitive-invalid-value'})
    assert response.status_code==422 and 'sensitive-invalid-value' not in response.text
