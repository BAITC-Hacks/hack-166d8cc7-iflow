from datetime import date
import hashlib
import json
from app.core.auth import Principal, require_self
from app.core.errors import DomainError
from app.schemas.responses import CompletionCommand, CompletionResult, SkillChange
from app.schemas.state import RuntimeCompletion, CompletionReceipt
from app.services.dataset import DatasetService
from .progress_engine import current_skills, effective_history
from .trajectory import build_trajectory
from .eligibility import REPEATABLE_EVENT_IDS

def normalized_command_fingerprint(principal: Principal,employee_id: str,event_id: str,command: CompletionCommand) -> str:
    data={"principal":principal.model_dump(),"employee_id":employee_id,"event_id":event_id,"command":command.model_dump(mode="json")}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def complete_activity(principal: Principal,employee_id: str,event_id: str,command: CompletionCommand,
                      dataset: DatasetService,as_of_date: date) -> CompletionResult:
    require_self(principal,employee_id)
    with dataset.lock:
        fingerprint=normalized_command_fingerprint(principal,employee_id,event_id,command)
        key=str(command.command_id)
        prior=dataset.state.receipts.get(key)
        if prior:
            if prior.request_fingerprint!=fingerprint: raise DomainError("conflict","Command ID already used")
            return prior.result
        snapshot=dataset.capture()
        employee=snapshot.employees.get(employee_id);event=snapshot.events.get(event_id)
        if employee is None or event is None: raise DomainError("not_found","Employee or event not found")
        history=effective_history(snapshot,employee_id)
        source=snapshot.history.get(command.source_record_id) if command.source_record_id else None
        if command.source_record_id:
            if source is None or source.employee_id!=employee_id or source.event_id!=event_id:
                raise DomainError("invalid","Participation does not belong to this employee and event")
            if any(c.source_record_id==source.record_id for c in snapshot.runtime_completions):
                raise DomainError("conflict","Participation already completed")
            if source.status not in ("in_progress","overdue"): raise DomainError("conflict","Participation cannot be completed")
            participation_date=source.date
            if command.session_date and command.session_date!=source.date: raise DomainError("invalid","Session date conflicts with participation")
        else:
            participation_date=command.session_date or as_of_date
            if event.format=="self_paced" and participation_date!=as_of_date:
                raise DomainError("invalid","Self-paced completion cannot be backdated")
            if event.format!="self_paced" and (command.session_date is None or participation_date not in event.upcoming_sessions):
                raise DomainError("invalid","Choose a known session")
            if any(r.event_id==event_id and r.date==participation_date for r in history):
                raise DomainError("conflict","Participation already exists; use its source record")
            current=current_skills(snapshot,employee_id,as_of_date)
            if not event.mandatory and (employee.role not in event.target_roles or employee.grade not in event.target_grades or any(current.get(k,0)<v for k,v in event.prerequisites.items())):
                raise DomainError("invalid","Activity entry requirements are not met")
        if participation_date>as_of_date: raise DomainError("invalid","Future participation cannot be completed")
        assigned_compliance=source is not None and event.mandatory and event.type=="compliance"
        if event_id not in REPEATABLE_EVENT_IDS and not assigned_compliance and any(r.event_id==event_id and r.status=="completed" for r in history):
            raise DomainError("conflict","Activity has already been completed")
        before=current_skills(snapshot,employee_id,as_of_date)
        row=RuntimeCompletion(command_id=command.command_id,employee_id=employee_id,event_id=event_id,
            source_record_id=command.source_record_id,participation_date=participation_date,completed_on=as_of_date)
        next_state=dataset.state.model_copy(update={"revision":dataset.state.revision+1,"completions":dataset.state.completions+(row,)})
        candidate=dataset.preview(next_state)
        after=current_skills(candidate,employee_id,as_of_date)
        result=CompletionResult(command_id=command.command_id,employee_id=employee_id,event_id=event_id,
            skill_changes=[SkillChange(skill_id=k,before=before.get(k,0),after=v,gain=v-before.get(k,0)) for k,v in sorted(after.items()) if v!=before.get(k,0)],
            trajectory=build_trajectory(employee_id,candidate,as_of_date),revision=next_state.revision,as_of_date=as_of_date)
        next_state=next_state.model_copy(update={"receipts":{**next_state.receipts,key:CompletionReceipt(request_fingerprint=fingerprint,result=result)}})
        try: dataset.commit(next_state)
        except OSError as error: raise DomainError("unavailable","Could not persist completion; retry with the same command ID") from error
        return result
