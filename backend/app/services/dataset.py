from threading import Lock
from app.repositories.dataset import DatasetSnapshot, build_snapshot
from app.repositories.state import StateRepository
from app.schemas.state import MutableState

class DatasetService:
    def __init__(self,snapshot: DatasetSnapshot,state_repository: StateRepository | None = None,raw_fingerprint: str = ""):
        self.raw_bundle=snapshot.bundle.model_copy(deep=True)
        self.lock=Lock()
        self.state_repository=state_repository
        self.state=state_repository.load(raw_fingerprint) if state_repository else MutableState(raw_fingerprint=raw_fingerprint)
        self._snapshot=self.preview(self.state)
    def capture(self) -> DatasetSnapshot:
        return self._snapshot
    def preview(self,state: MutableState) -> DatasetSnapshot:
        state=MutableState.model_validate(state.model_dump())
        bundle=self.raw_bundle.model_copy(update={
            "employees":self.raw_bundle.employees+state.imported_employees,
            "history":self.raw_bundle.history+state.imported_history})
        from .progress_engine import validate_runtime
        snapshot=build_snapshot(bundle,state.revision,state.completions)
        validate_runtime(snapshot)
        return snapshot
    def commit(self,next_state: MutableState) -> DatasetSnapshot:
        # Caller holds the single mutation lock from read through publication.
        if next_state==self.state: return self._snapshot
        candidate=self.preview(next_state)
        if self.state_repository is None: raise RuntimeError("State repository is required for mutations")
        self.state_repository.save(next_state)
        self.state=next_state
        self._snapshot=candidate
        return candidate

def import_dataset(principal,employees,history,dataset: DatasetService):
    from app.core.auth import require_hr
    from app.core.errors import DomainError
    from app.schemas.responses import ImportResult
    from app.services.progress_engine import effective_history
    from app.services.eligibility import REPEATABLE_EVENT_IDS
    require_hr(principal)
    if employees is None and history is None: raise DomainError("invalid","Provide employees.json or activity_history.csv")
    with dataset.lock:
        snapshot=dataset.capture()
        def reject(code,message,file,row=None,field=None):
            loc=[file]
            if row is not None: loc.append(row)
            if field is not None: loc.append(field)
            raise DomainError(code,message,[{"loc":loc,"type":code,"message":message}])
        if employees is not None and employees.meta!=snapshot.meta:
            reject("invalid","Dataset metadata must match the current source","employees.json",field="meta")
        added_employees=[];added_history=[];unchanged_employees=0;unchanged_history=0
        incoming_employees=employees.employees if employees is not None else ()
        incoming_history=history if history is not None else ()
        known_employees={e.employee_id for e in snapshot.employees.list()}|{e.employee_id for e in incoming_employees}
        profiles={(p.role,p.grade) for p in snapshot.bundle.role_profiles}
        known_skills={s.skill_id for s in snapshot.bundle.skills}
        seen=set()
        for index,row in enumerate(incoming_employees):
            def invalid(field,message):
                reject("invalid",message,"employees.json",index,field)
            if row.employee_id in seen: invalid("employee_id","Duplicate ID within upload")
            seen.add(row.employee_id)
            if (row.role,row.grade) not in profiles: invalid("role/grade","Unknown role/grade")
            if row.manager_id is not None and row.manager_id not in known_employees: invalid("manager_id","Unknown manager")
            if not set(row.skills)<=known_skills: invalid("skills","Unknown skill")
            if row.hire_date>snapshot.meta.as_of_date: invalid("hire_date","Future hire date")
            if row.last_review_date>snapshot.meta.as_of_date: invalid("last_review_date","Future assessment date")
            if row.career_goal and (row.career_goal.target_role,row.career_goal.target_grade) not in profiles: invalid("career_goal","Unknown career goal")
            old=snapshot.employees.get(row.employee_id)
            if old is not None:
                if old!=row: reject("conflict","Employee ID has different source content","employees.json",index,"employee_id")
                unchanged_employees+=1
            else: added_employees.append(row)
        seen=set()
        for line,row in enumerate(incoming_history,start=2):
            def history_error(code,field,message):
                reject(code,message,"activity_history.csv",line,field)
            if row.record_id in seen: history_error("invalid","record_id","Duplicate ID within upload")
            seen.add(row.record_id)
            if row.employee_id not in known_employees: history_error("invalid","employee_id","Unknown employee")
            if snapshot.events.get(row.event_id) is None: history_error("invalid","event_id","Unknown event")
            if row.date>snapshot.meta.as_of_date: history_error("invalid","date","Future historical participation")
            old=snapshot.history.get(row.record_id)
            if old is not None:
                if old!=row: history_error("conflict","record_id","History ID has different source content")
                unchanged_history+=1
                continue
            previous=effective_history(snapshot,row.employee_id)
            same_participation=any(r.event_id==row.event_id and r.date==row.date for r in previous)
            same_participation|=any((r.employee_id,r.event_id,r.date)==(row.employee_id,row.event_id,row.date) for r in added_history)
            if same_participation: history_error("conflict","record_id","Participation already exists under a different record ID")
            event=snapshot.events.get(row.event_id)
            compliance=event is not None and event.mandatory and event.type=="compliance" and not event.develops_skills
            if row.status=="completed" and row.event_id not in REPEATABLE_EVENT_IDS and not compliance:
                completed=any(r.event_id==row.event_id and r.status=="completed" for r in previous)
                completed|=any(r.employee_id==row.employee_id and r.event_id==row.event_id and r.status=="completed" for r in added_history)
                if completed: history_error("conflict","event_id","Non-recurring activity already completed")
            added_history.append(row)
        if added_employees or added_history:
            next_state=dataset.state.model_copy(update={"revision":dataset.state.revision+1,
                "imported_employees":dataset.state.imported_employees+tuple(added_employees),
                "imported_history":dataset.state.imported_history+tuple(added_history)})
            try: dataset.commit(next_state)
            except ValueError as err: raise DomainError("invalid","Prospective dataset contains invalid references or values") from err
            except OSError as err: raise DomainError("unavailable","Could not persist import; no changes applied") from err
        return ImportResult(added_employees=len(added_employees),unchanged_employees=unchanged_employees,
            added_history=len(added_history),unchanged_history=unchanged_history,
            revision=dataset.state.revision,as_of_date=snapshot.meta.as_of_date)
