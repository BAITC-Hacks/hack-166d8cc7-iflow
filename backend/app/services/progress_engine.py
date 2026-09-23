from collections.abc import Mapping, Sequence
from datetime import date
from app.schemas.employee import Employee
from app.schemas.activity import SkillGain
from app.schemas.history import ActivityHistory, EffectiveCompletion, ParticipationView
from app.repositories.events import EventRepository

def apply_gains(current: Mapping[str,int], gains: Sequence[SkillGain]) -> dict[str,int]:
    result = dict(current)
    for gain in gains:
        old = result.get(gain.skill_id,0)
        result[gain.skill_id] = max(old,min(old+gain.gain,gain.max_level))
    return result

def historical_completions(history: Sequence[ActivityHistory]) -> list[EffectiveCompletion]:
    return [EffectiveCompletion(completion_key=r.record_id,event_id=r.event_id,completed_on=r.date)
            for r in history if r.status=="completed"]

def project_skills(employee: Employee, completions: Sequence[EffectiveCompletion],
                   events: EventRepository, as_of_date: date) -> dict[str,int]:
    levels = dict(employee.skills)
    seen: set[str] = set()
    for row in sorted(completions,key=lambda c:(c.completed_on,c.completion_key)):
        if row.completion_key in seen: continue
        seen.add(row.completion_key)
        if employee.last_review_date < row.completed_on <= as_of_date:
            event=events.get(row.event_id)
            if event is None: raise ValueError("Unknown completion event")
            levels=apply_gains(levels,event.develops_skills)
    return levels

def participation_views(history: Sequence[ActivityHistory]) -> list[ParticipationView]:
    return [ParticipationView(source_record_id=r.record_id,event_id=r.event_id,date=r.date,
        status=r.status,completed_on=r.date if r.status=="completed" else None,source=r) for r in history]

def effective_history(snapshot, employee_id: str) -> list[ParticipationView]:
    rows=participation_views(snapshot.history.for_employee(employee_id))
    for c in snapshot.runtime_completions:
        if c.employee_id!=employee_id: continue
        if c.source_record_id:
            rows=[r for r in rows if r.source_record_id!=c.source_record_id]
        source=snapshot.history.get(c.source_record_id) if c.source_record_id else None
        rows.append(ParticipationView(source_record_id=c.source_record_id or "runtime:"+str(c.command_id),
            event_id=c.event_id,date=c.participation_date,status="completed",completed_on=c.completed_on,source=source))
    return sorted(rows,key=lambda r:(r.date,r.source_record_id or ""))

def current_skills(snapshot,employee_id: str,as_of_date: date) -> dict[str,int]:
    employee=snapshot.employees.get(employee_id)
    if employee is None: raise LookupError("Employee not found")
    completions=[EffectiveCompletion(completion_key=r.source_record_id,event_id=r.event_id,completed_on=r.completed_on)
                 for r in effective_history(snapshot,employee_id) if r.status=="completed"]
    return project_skills(employee,completions,snapshot.events,as_of_date)

def validate_runtime(snapshot) -> None:
    seen_commands=set()
    seen_participations=set()
    seen_sources=set()
    for c in snapshot.runtime_completions:
        if c.command_id in seen_commands: raise ValueError("Duplicate completion command")
        seen_commands.add(c.command_id)
        key=(c.employee_id,c.event_id,c.participation_date)
        if key in seen_participations: raise ValueError("Duplicate runtime participation")
        seen_participations.add(key)
        if snapshot.employees.get(c.employee_id) is None or snapshot.events.get(c.event_id) is None:
            raise ValueError("Unknown runtime reference")
        if c.completed_on<c.participation_date or c.completed_on<snapshot.meta.as_of_date:
            raise ValueError("Invalid runtime completion date")
        if c.source_record_id:
            src=snapshot.history.get(c.source_record_id)
            if c.source_record_id in seen_sources or src is None or (src.employee_id,src.event_id,src.date)!=key or src.status not in ("in_progress","overdue"):
                raise ValueError("Invalid runtime source transition")
            seen_sources.add(c.source_record_id)
        elif any((r.employee_id,r.event_id,r.date)==key for r in snapshot.history.for_employee(c.employee_id)):
            raise ValueError("Runtime participation duplicates source history")
