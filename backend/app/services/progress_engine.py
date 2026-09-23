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
