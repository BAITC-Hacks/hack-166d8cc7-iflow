from datetime import date
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from app.core.auth import Principal
from app.core.errors import DomainError
from app.repositories.dataset import build_snapshot
from app.repositories.state import StateRepository
from app.services.dataset import DatasetService

@pytest.fixture
def dataset(tiny_bundle,tmp_path):
    return DatasetService(build_snapshot(tiny_bundle),StateRepository(tmp_path/"state.json"),"hash")

def run(dataset,clock,**changes):
    from app.schemas.responses import CompletionCommand
    from app.services.completion import complete_activity
    args=dict(principal=Principal(role="employee",employee_id="TEST_EMP"),employee_id="TEST_EMP",event_id="EV_012",
              command=CompletionCommand(command_id=uuid4()),dataset=dataset,as_of_date=clock)
    args.update(changes)
    return complete_activity(**args)

def test_retry_after_restart_returns_receipt(dataset,clock):
    from app.schemas.responses import CompletionCommand
    cmd=CompletionCommand(command_id=uuid4())
    first=run(dataset,clock,command=cmd)
    restarted=DatasetService(build_snapshot(dataset.raw_bundle),dataset.state_repository,"hash")
    assert run(restarted,clock,command=cmd)==first
    assert restarted.state.revision==1 and len(restarted.state.completions)==1
    assert first.skill_changes[0].gain==1

def test_changed_command_with_same_id_conflicts(dataset,clock):
    from app.schemas.responses import CompletionCommand
    cmd=CompletionCommand(command_id=uuid4());run(dataset,clock,command=cmd)
    with pytest.raises(DomainError) as err: run(dataset,clock,command=cmd,event_id="other")
    assert err.value.code=="conflict"

def test_different_id_same_nonrecurring_event_conflicts(dataset,clock):
    run(dataset,clock)
    with pytest.raises(DomainError) as err: run(dataset,clock)
    assert err.value.code=="conflict"

@pytest.mark.parametrize("principal",[Principal(role="hr"),Principal(role="employee",employee_id="other")])
def test_other_employee_and_hr_denied(dataset,clock,principal):
    with pytest.raises(DomainError) as err: run(dataset,clock,principal=principal)
    assert err.value.code=="forbidden"

def test_unknown_event(dataset,clock):
    with pytest.raises(DomainError) as err: run(dataset,clock,event_id="unknown")
    assert err.value.code=="not_found"

def test_self_paced_cannot_be_backdated(dataset,clock):
    from app.schemas.responses import CompletionCommand
    with pytest.raises(DomainError): run(dataset,clock,command=CompletionCommand(command_id=uuid4(),session_date=date(2026,9,1)))

@pytest.mark.parametrize("status,pct,allowed",[("in_progress",40,True),("overdue",0,True),("dropped",10,False),("completed",100,False),("no_show",0,False)])
def test_source_transition(status,pct,allowed,tiny_bundle,make_history,tmp_path,clock):
    from app.schemas.responses import CompletionCommand
    b=tiny_bundle.model_copy(update={"history":(make_history(status=status,completion_pct=pct),)})
    ds=DatasetService(build_snapshot(b),StateRepository(tmp_path/"s.json"),"h")
    cmd=CompletionCommand(command_id=uuid4(),source_record_id="TEST_REC")
    if not allowed:
        with pytest.raises(DomainError): run(ds,clock,command=cmd)
    else:
        result=run(ds,clock,command=cmd)
        assert result.skill_changes[0].after==2
        with pytest.raises(DomainError): run(ds,clock,command=cmd.model_copy(update={"command_id":uuid4()}))

def test_existing_assignment_can_finish_without_current_prerequisite(tiny_bundle,make_history,make_event,tmp_path,clock):
    from app.schemas.responses import CompletionCommand
    b=tiny_bundle.model_copy(update={"events":(make_event(prerequisites={"SK_PYTHON":4}),),"history":(make_history(status="in_progress",completion_pct=40),)})
    ds=DatasetService(build_snapshot(b),StateRepository(tmp_path/"s.json"),"h")
    assert run(ds,clock,command=CompletionCommand(command_id=uuid4(),source_record_id="TEST_REC")).skill_changes[0].after==2

def test_recurring_sessions(tiny_bundle,make_event,tmp_path):
    from app.schemas.responses import CompletionCommand
    b=tiny_bundle.model_copy(update={"events":(make_event(event_id="EV_036",format="online",upcoming_sessions=["2026-10-01","2026-10-02"]),)})
    ds=DatasetService(build_snapshot(b),StateRepository(tmp_path/"s.json"),"h")
    c=CompletionCommand(command_id=uuid4(),session_date=date(2026,10,1))
    run(ds,date(2026,10,1),event_id="EV_036",command=c)
    with pytest.raises(DomainError): run(ds,date(2026,10,1),event_id="EV_036",command=c.model_copy(update={"command_id":uuid4()}))
    result=run(ds,date(2026,10,2),event_id="EV_036",command=CompletionCommand(command_id=uuid4(),session_date=date(2026,10,2)))
    assert result.skill_changes[0].after==3

@pytest.mark.parametrize("session",["2026-11-01","2026-09-30"])
def test_future_or_unknown_session(tiny_bundle,make_event,tmp_path,clock,session):
    from app.schemas.responses import CompletionCommand
    b=tiny_bundle.model_copy(update={"events":(make_event(format="online",upcoming_sessions=["2026-11-01"]),)})
    ds=DatasetService(build_snapshot(b),StateRepository(tmp_path/"s.json"),"h")
    with pytest.raises(DomainError): run(ds,clock,command=CompletionCommand(command_id=uuid4(),session_date=session))

def test_two_simultaneous_identical_commands_apply_once(dataset,clock):
    from app.schemas.responses import CompletionCommand
    cmd=CompletionCommand(command_id=uuid4());barrier=Barrier(2)
    def worker(): barrier.wait();return run(dataset,clock,command=cmd)
    with ThreadPoolExecutor(2) as pool: results=list(pool.map(lambda _:worker(),range(2)))
    assert results[0]==results[1] and dataset.state.revision==1

def test_save_failure_then_retry_applies_once(dataset,clock,monkeypatch):
    original=dataset.state_repository.save
    def fail(state): raise OSError("disk")
    monkeypatch.setattr(dataset.state_repository,"save",fail)
    with pytest.raises(DomainError) as err: run(dataset,clock)
    assert err.value.code=="unavailable" and dataset.state.revision==0
    monkeypatch.setattr(dataset.state_repository,"save",original)
    assert run(dataset,clock).skill_changes[0].after==2

def test_mandatory_existing_compliance_can_repeat_without_gains(tiny_bundle,make_event,make_history,tmp_path,clock):
    from app.schemas.responses import CompletionCommand
    e=make_event(mandatory=True,type="compliance",develops_skills=[])
    h=(make_history(record_id="past",date=date(2025,1,1)),make_history(status="overdue",completion_pct=0))
    ds=DatasetService(build_snapshot(tiny_bundle.model_copy(update={"events":(e,),"history":h})),StateRepository(tmp_path/"s.json"),"h")
    assert run(ds,clock,command=CompletionCommand(command_id=uuid4(),source_record_id="TEST_REC")).skill_changes==[]

def test_source_record_wrong_event_rejected(dataset,clock):
    from app.schemas.responses import CompletionCommand
    with pytest.raises(DomainError): run(dataset,clock,command=CompletionCommand(command_id=uuid4(),source_record_id="unknown"))
