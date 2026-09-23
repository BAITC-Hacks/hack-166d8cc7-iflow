import hashlib
import json
from pathlib import Path
import pytest

RAW = Path(__file__).resolve().parents[2] / "data/raw"

def load():
    from app.repositories.dataset import DatasetRepository
    return DatasetRepository(RAW).load()

def test_real_dataset_counts():
    b = load()
    assert [len(getattr(b, x)) for x in ("employees","events","skills","role_profiles","history")] == [200,40,60,32,2743]
    assert str(b.meta.as_of_date) == "2026-10-01"

def test_employee_roundtrip_preserves_all_fields():
    b = load()
    assert b.employees[0].model_dump(mode="json") == json.loads((RAW/"employees.json").read_bytes())["employees"][0]

def test_csv_blank_fields_are_none():
    assert load().history[0].due_date is None
    assert load().history[0].feedback_rating == 5

@pytest.mark.parametrize("kind", ["skill", "employee", "event", "manager", "role", "grade", "goal", "duplicate", "metadata"])
def test_invalid_dataset_rejected(kind):
    from app.repositories.dataset import build_snapshot
    from app.schemas.dataset import SourceBundle
    b = load().model_dump(mode="json")
    if kind == "skill": b["employees"][0]["skills"]["UNKNOWN"] = 2
    if kind == "employee": b["history"][0]["employee_id"] = "UNKNOWN"
    if kind == "event": b["history"][0]["event_id"] = "UNKNOWN"
    if kind == "manager": b["employees"][0]["manager_id"] = "UNKNOWN"
    if kind == "role": b["employees"][0]["role"] = "UNKNOWN"
    if kind == "grade": b["employees"][0]["grade"] = "UNKNOWN"
    if kind == "goal": b["employees"][0]["career_goal"]["target_role"] = "UNKNOWN"
    if kind == "duplicate": b["employees"].append(b["employees"][0])
    if kind == "metadata": b["history"][0]["date"] = "2030-01-01"
    with pytest.raises(ValueError):
        build_snapshot(SourceBundle.model_validate(b))

def test_unknown_fields_rejected():
    from app.schemas.employee import Employee
    with pytest.raises(ValueError):
        Employee.model_validate({**load().employees[0].model_dump(), "invented": True})

def test_unknown_employee_returns_none():
    from app.repositories.dataset import build_snapshot
    assert build_snapshot(load()).employees.get("UNKNOWN") is None

def test_raw_hashes_match_manifest():
    manifest = json.loads((RAW.parent/"fixtures/raw-sha256.json").read_text())
    for filename, expected in manifest.items():
        assert hashlib.sha256((RAW/filename).read_bytes()).hexdigest() == expected

def test_metadata_mismatch_rejected(tmp_path):
    from app.repositories.dataset import DatasetRepository
    for path in RAW.glob("*"):
        if path.is_file(): (tmp_path/path.name).write_bytes(path.read_bytes())
    body = json.loads((tmp_path/"events.json").read_bytes())
    body["meta"]["as_of_date"] = "2027-01-01"
    (tmp_path/"events.json").write_text(json.dumps(body))
    with pytest.raises(ValueError):
        DatasetRepository(tmp_path).load()
