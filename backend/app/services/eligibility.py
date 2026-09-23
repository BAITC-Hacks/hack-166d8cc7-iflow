from collections.abc import Mapping, Sequence
from datetime import date
from app.schemas.employee import Employee
from app.schemas.activity import Event
from app.schemas.history import ParticipationView
from app.schemas.responses import TargetAnalysis
from app.schemas.recommendation import RecommendationCandidate, RecommendationFactor as Factor, EligibilityResult

REPEATABLE_EVENT_IDS = frozenset({"EV_036"})

def evaluate_event(employee: Employee,current: Mapping[str,int],targets: Sequence[TargetAnalysis],
    history: Sequence[ParticipationView],event: Event,as_of_date: date,
    repeatable_event_ids: frozenset[str] = REPEATABLE_EVENT_IDS) -> RecommendationCandidate:
    reasons=[]
    if event.mandatory: reasons.append("mandatory")
    if employee.role not in event.target_roles: reasons.append("audience_role")
    if employee.grade not in event.target_grades: reasons.append("audience_grade")
    if any(current.get(k,0)<v for k,v in event.prerequisites.items()): reasons.append("prerequisites")
    sessions=sorted(d for d in event.upcoming_sessions if d>=as_of_date)
    next_session=sessions[0] if sessions else None
    if event.format!="self_paced" and next_session is None: reasons.append("unavailable")
    matched=[r for r in history if r.event_id==event.event_id]
    completed=[r for r in matched if r.status=="completed"]
    if completed and event.event_id not in repeatable_event_ids: reasons.append("already_completed")
    gains={g.skill_id:max(0,min(current.get(g.skill_id,0)+g.gain,g.max_level)-current.get(g.skill_id,0)) for g in event.develops_skills}
    if not any(g.gap>0 and gains.get(g.skill_id,0)>0 for t in targets for g in t.gaps): reasons.append("no_target_gain")
    factors=[Factor(kind="current_grade",values={"role":employee.role,"grade":employee.grade},source_ids=[employee.employee_id])]
    for target in targets:
        factors.append(Factor(kind="target_grade",values={"role":target.role,"grade":target.grade},source_ids=[target.role+":"+target.grade]))
        for gap in target.gaps:
            if gap.skill_id not in gains: continue
            values={"role":target.role,"grade":target.grade,"skill_id":gap.skill_id}
            factors.extend([
                Factor(kind="skill_levels",values={**values,"current":gap.current_level,"required":gap.required_level},source_ids=[gap.skill_id]),
                Factor(kind="critical_skill",values={**values,"critical":gap.is_critical},source_ids=[gap.skill_id]),
                Factor(kind="attainable_gain",values={"skill_id":gap.skill_id,"gain":gains[gap.skill_id]},source_ids=[event.event_id,gap.skill_id])])
    factors.extend([
        Factor(kind="completed_history",values={"count":len(completed)},source_ids=[r.source_record_id for r in completed if r.source_record_id]),
        Factor(kind="participation_outcomes",values={s:sum(r.status==s for r in matched) for s in ("no_show","declined","dropped")},
               source_ids=[r.source_record_id for r in matched if r.status in ("no_show","declined","dropped") and r.source_record_id]),
        Factor(kind="availability",values={"format":event.format,"next_session":str(next_session) if next_session else None,"as_of_date":str(as_of_date)},source_ids=[event.event_id]),
        Factor(kind="duration_format",values={"hours":event.duration_hours,"format":event.format},source_ids=[event.event_id])])
    return RecommendationCandidate(event_id=event.event_id,title=event.title,possible_skill_gains=gains,
        eligibility=EligibilityResult(eligible=not reasons,reasons=reasons,next_session=next_session),factors=factors)
