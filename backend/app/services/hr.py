from collections import Counter
from datetime import date
from app.repositories.dataset import DatasetSnapshot
from app.schemas.responses import HRDashboard, SkillGapCount, ParticipationCount
from .trajectory import build_trajectory
from .progress_engine import effective_history

def build_hr_dashboard(snapshot: DatasetSnapshot,as_of_date: date) -> HRDashboard:
    counts=Counter()
    participation={e.event_id:Counter() for e in snapshot.events.list()}
    without=[]
    for employee in snapshot.employees.list():
        trajectory=build_trajectory(employee.employee_id,snapshot,as_of_date)
        for gap in trajectory.next_grade_gaps:
            if gap.gap>0: counts[gap.skill_id]+=1
        if not trajectory.candidates: without.append(employee.employee_id)
        for row in effective_history(snapshot,employee.employee_id):
            participation[row.event_id][row.status]+=1
    return HRDashboard(skill_gap_counts=[SkillGapCount(skill_id=k,name=snapshot.skills.get(k).name,employee_count=v) for k,v in sorted(counts.items())],
        participation_by_event=[ParticipationCount(event_id=k,title=snapshot.events.get(k).title,status_counts=dict(v)) for k,v in sorted(participation.items())],
        employees_without_candidate=sorted(without),recommendation_status="not_implemented",
        employees_without_recommendation=None,revision=snapshot.revision,as_of_date=as_of_date)
