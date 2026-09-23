from datetime import date
from uuid import uuid4
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.core.auth import Principal
from app.core.errors import DomainError
from app.schemas.dataset import EmployeesDataset
from app.repositories.dataset import build_snapshot
from app.repositories.state import StateRepository
from app.services.dataset import DatasetService

HR=Principal(role="hr")

@pytest.fixture
def dataset(tiny_bundle,tmp_path):
    return DatasetService(build_snapshot(tiny_bundle),StateRepository(tmp_path/"state.json"),"hash")

def imp(dataset,employees=None,history=None):
    from app.services.dataset import import_dataset
    return import_dataset(HR,employees,history,dataset)

def doc(dataset,employee):
    return EmployeesDataset(meta=dataset.capture().meta,employees=(employee,))

def test_invalid_history_rolls_back_employee(dataset,make_employee,make_history):
    before=dataset.capture()
    with pytest.raises(DomainError):
        imp(dataset,doc(dataset,make_employee(employee_id="JURY_NEW")), (make_history(employee_id="JURY_NEW",event_id="UNKNOWN"),))
    assert dataset.capture() is before and not dataset.state_repository.path.exists()
    assert dataset.capture().employees.get("JURY_NEW") is None

def test_identical_reimport_is_noop(dataset,make_employee,make_history):
    employees=doc(dataset,make_employee(employee_id="JURY_NEW"))
    history=(make_history(employee_id="JURY_NEW"),)
    r=imp(dataset,employees,history);again=imp(dataset,employees,history)
    assert r.added_employees==1 and r.added_history==1
    assert again.unchanged_employees==1 and again.unchanged_history==1 and again.revision==1

def test_changed_existing_employee_conflicts(dataset,make_employee):
    with pytest.raises(DomainError) as e: imp(dataset,doc(dataset,make_employee(full_name="changed")))
    assert e.value.code=="conflict"

def test_changed_existing_history_conflicts(dataset,make_history):
    imp(dataset,history=(make_history(),))
    with pytest.raises(DomainError) as e: imp(dataset,history=(make_history(score=99),))
    assert e.value.code=="conflict"

def test_duplicate_id_inside_upload(dataset,make_employee):
    e=make_employee(employee_id="NEW")
    with pytest.raises(DomainError) as err: imp(dataset,EmployeesDataset(meta=dataset.capture().meta,employees=(e,e)))
    assert err.value.code=="invalid"

@pytest.mark.parametrize("kind",["participation","repeat"])
def test_semantic_collision(dataset,make_history,kind):
    imp(dataset,history=(make_history(),))
    with pytest.raises(DomainError) as err:
        imp(dataset,history=(make_history(record_id="new",date=date(2026,9,21) if kind=="repeat" else date(2026,9,20)),))
    assert err.value.code=="conflict"

def test_new_employees_can_reference_each_other(dataset,make_employee):
    a=make_employee(employee_id="A",manager_id="B")
    b=make_employee(employee_id="B",grade="Lead",manager_id=None)
    r=imp(dataset,EmployeesDataset(meta=dataset.capture().meta,employees=(a,b)))
    assert r.added_employees==2

def test_metadata_mismatch(dataset,make_employee):
    d=doc(dataset,make_employee(employee_id="NEW")).model_copy(update={"meta":dataset.capture().meta.model_copy(update={"version":"2"})})
    with pytest.raises(DomainError): imp(dataset,d)

def test_completed_before_review_is_not_replayed(dataset,make_history,clock):
    from app.services.progress_engine import current_skills
    imp(dataset,history=(make_history(date=date(2026,8,1)),))
    assert current_skills(dataset.capture(),"TEST_EMP",clock)["SK_PYTHON"]==1

def test_reimport_source_after_runtime_transition_keeps_one_gain(dataset,make_history,clock):
    from app.services.completion import complete_activity
    from app.schemas.responses import CompletionCommand
    from app.services.progress_engine import current_skills
    h=make_history(status="in_progress",completion_pct=40)
    imp(dataset,history=(h,))
    complete_activity(Principal(role="employee",employee_id="TEST_EMP"),"TEST_EMP","EV_012",
        CompletionCommand(command_id=uuid4(),source_record_id=h.record_id),dataset,clock)
    result=imp(dataset,history=(h,))
    assert result.revision==2 and current_skills(dataset.capture(),"TEST_EMP",clock)["SK_PYTHON"]==2

def test_import_conflicting_runtime_participation(dataset,make_history,clock):
    from app.services.completion import complete_activity
    from app.schemas.responses import CompletionCommand
    complete_activity(Principal(role="employee",employee_id="TEST_EMP"),"TEST_EMP","EV_012",CompletionCommand(command_id=uuid4()),dataset,clock)
    with pytest.raises(DomainError) as e: imp(dataset,history=(make_history(date=clock),))
    assert e.value.code=="conflict"

def test_failed_persistence_no_publication(dataset,make_employee,monkeypatch):
    def fail(*args): raise OSError("disk")
    monkeypatch.setattr(dataset.state_repository,"save",fail)
    with pytest.raises(DomainError) as e: imp(dataset,doc(dataset,make_employee(employee_id="NEW")))
    assert e.value.code=="unavailable" and dataset.capture().revision==0

def test_no_payload(dataset):
    with pytest.raises(DomainError): imp(dataset)

def test_late_invalid_row_preserves_state_file(dataset,make_history,make_employee):
    imp(dataset,doc(dataset,make_employee(employee_id="NEW")))
    before=dataset.state_repository.path.read_bytes()
    with pytest.raises(DomainError): imp(dataset,history=(make_history(),make_history(record_id="bad",event_id="unknown")))
    assert dataset.state_repository.path.read_bytes()==before and dataset.state.revision==1

def test_concurrent_import_and_completion_preserve_both(dataset,make_employee,clock):
    from app.services.completion import complete_activity
    from app.schemas.responses import CompletionCommand
    barrier=Barrier(2)
    def import_worker():
        barrier.wait();return imp(dataset,doc(dataset,make_employee(employee_id="NEW")))
    def complete_worker():
        barrier.wait();return complete_activity(Principal(role="employee",employee_id="TEST_EMP"),"TEST_EMP","EV_012",CompletionCommand(command_id=uuid4()),dataset,clock)
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(import_worker);b=pool.submit(complete_worker);a.result();b.result()
    restarted=DatasetService(build_snapshot(dataset.raw_bundle),dataset.state_repository,"hash")
    assert restarted.capture().revision==2 and restarted.capture().employees.get("NEW") is not None
    assert len(restarted.state.completions)==1
