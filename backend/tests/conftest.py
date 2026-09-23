from pathlib import Path
from datetime import date
import pytest
from app.repositories.dataset import DatasetRepository, build_snapshot
from app.schemas.employee import Employee
from app.schemas.activity import Event
from app.schemas.history import ActivityHistory

@pytest.fixture(scope="session")
def real_bundle():
    return DatasetRepository(Path(__file__).resolve().parents[2]/"data/raw").load()

@pytest.fixture
def make_employee(real_bundle):
    def make(**changes):
        raw = real_bundle.employees[0].model_dump()
        raw.update(employee_id="TEST_EMP", manager_id=None, grade="Middle",
                   skills={"SK_PYTHON":1}, last_review_date=date(2026,9,1))
        raw.update(changes)
        return Employee.model_validate(raw)
    return make

@pytest.fixture
def make_event(real_bundle):
    def make(**changes):
        raw = next(r for r in real_bundle.events if r.event_id=="EV_012").model_dump()
        raw.update(changes)
        return Event.model_validate(raw)
    return make

@pytest.fixture
def make_history():
    def make(**changes):
        raw = dict(record_id="TEST_REC", employee_id="TEST_EMP", event_id="EV_012",
            date=date(2026,9,20), due_date=None, status="completed", completion_pct=100,
            score=None, feedback_rating=None, assigned_by="self")
        raw.update(changes)
        return ActivityHistory.model_validate(raw)
    return make

@pytest.fixture
def tiny_bundle(real_bundle, make_employee, make_event):
    return real_bundle.model_copy(update={"employees":(make_employee(),),"events":(make_event(),),"history":()})

@pytest.fixture
def events(tiny_bundle): return build_snapshot(tiny_bundle).events

@pytest.fixture
def skills(tiny_bundle): return build_snapshot(tiny_bundle).skills

@pytest.fixture
def clock(): return date(2026,10,1)
