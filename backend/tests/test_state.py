import pytest
from app.repositories.dataset import build_snapshot

def state_repo(tmp_path):
    from app.repositories.state import StateRepository
    return StateRepository(tmp_path/"state.json")

def test_missing_state_starts_empty(tmp_path):
    state=state_repo(tmp_path).load("hash")
    assert state.revision==0 and state.imported_employees==() and state.completions==()

def test_invalid_json_fails_startup(tmp_path):
    repo=state_repo(tmp_path);repo.path.write_text("{bad")
    with pytest.raises(ValueError): repo.load("hash")

def test_raw_fingerprint_mismatch_fails(tmp_path):
    repo=state_repo(tmp_path);repo.save(repo.load("hash"))
    with pytest.raises(ValueError): repo.load("other")

def test_roundtrip_state(tmp_path):
    repo=state_repo(tmp_path);state=repo.load("hash");repo.save(state)
    assert repo.load("hash")==state

def test_failed_replace_preserves_file(tmp_path,monkeypatch):
    repo=state_repo(tmp_path);state=repo.load("hash");repo.save(state);before=repo.path.read_bytes()
    def fail(*args): raise OSError("simulated")
    monkeypatch.setattr("app.repositories.state.os.replace",fail)
    with pytest.raises(OSError): repo.save(state.model_copy(update={"revision":1}))
    assert repo.path.read_bytes()==before

def test_failed_save_does_not_publish_snapshot(tmp_path,tiny_bundle,monkeypatch):
    from app.services.dataset import DatasetService
    repo=state_repo(tmp_path);service=DatasetService(build_snapshot(tiny_bundle),repo,"hash")
    before=service.capture()
    def fail(*args): raise OSError("simulated")
    monkeypatch.setattr(repo,"save",fail)
    with pytest.raises(OSError): service.commit(service.state.model_copy(update={"revision":1}))
    assert service.capture() is before and service.state.revision==0

def test_captured_snapshot_retains_old_runtime(tmp_path,tiny_bundle):
    from app.schemas.state import RuntimeCompletion
    from app.services.dataset import DatasetService
    service=DatasetService(build_snapshot(tiny_bundle),state_repo(tmp_path),"hash")
    before=service.capture()
    row=RuntimeCompletion(command_id="00000000-0000-0000-0000-000000000001",employee_id="TEST_EMP",event_id="EV_012",source_record_id=None,participation_date="2026-10-01",completed_on="2026-10-01")
    service.commit(service.state.model_copy(update={"revision":1,"completions":(row,)}))
    assert before.revision==0 and before.runtime_completions==()
    assert service.capture().runtime_completions==(row,)

def test_noop_does_not_increment_revision(tmp_path,tiny_bundle):
    from app.services.dataset import DatasetService
    service=DatasetService(build_snapshot(tiny_bundle),state_repo(tmp_path),"hash")
    service.commit(service.state)
    assert service.capture().revision==0
