from collections import Counter
from datetime import date
from app.repositories.dataset import DatasetSnapshot
from app.schemas.responses import HRDashboard, SkillGapCount, ParticipationCount
from .trajectory import build_trajectory
from .progress_engine import effective_history

def build_hr_dashboard(snapshot: DatasetSnapshot,as_of_date: date, recommendation_states=None) -> HRDashboard:
    counts=Counter()
    participation={e.event_id:Counter() for e in snapshot.events.list()}
    without=[]
    uncovered=[]
    states = recommendation_states or {}
    for employee in snapshot.employees.list():
        trajectory=build_trajectory(employee.employee_id,snapshot,as_of_date)
        for gap in trajectory.next_grade_gaps:
            if gap.gap>0: counts[gap.skill_id]+=1
        if not trajectory.candidates: without.append(employee.employee_id)
        targets = [(employee.role, trajectory.next_grade, trajectory.next_grade_gaps)]
        if trajectory.career_goal_analysis:
            goal = trajectory.career_goal_analysis
            targets.append((goal.role, goal.grade, goal.gaps))
        for role, grade, gaps in targets:
            for gap in gaps:
                if gap.gap <= 0 or not gap.is_critical:
                    continue
                # Coverage of currently eligible catalog, respecting every cap.
                reachable = gap.current_level
                growths = [g for c in trajectory.candidates for g in snapshot.events.get(c.event_id).develops_skills if g.skill_id == gap.skill_id]
                for g in sorted(growths, key=lambda g: g.max_level):
                    reachable = max(reachable, min(reachable + g.gain, g.max_level))
                if reachable < gap.required_level:
                    row = dict(employee_id=employee.employee_id, role=role, grade=grade,
                        skill_id=gap.skill_id, name=gap.name, current_level=gap.current_level,
                        required_level=gap.required_level, attainable_level=reachable)
                    if row not in uncovered: uncovered.append(row)
        for row in effective_history(snapshot,employee.employee_id):
            participation[row.event_id][row.status]+=1
    return HRDashboard(skill_gap_counts=[SkillGapCount(skill_id=k,name=snapshot.skills.get(k).name,employee_count=v) for k,v in sorted(counts.items())],
        participation_by_event=[ParticipationCount(event_id=k,title=snapshot.events.get(k).title,status_counts=dict(v)) for k,v in sorted(participation.items())],
        employees_without_candidate=sorted(without),recommendation_status="available",
        employees_without_recommendation=sorted(e.employee_id for e in snapshot.employees.list() if states.get(e.employee_id) != "ready"),
        recommendation_states={e.employee_id:states.get(e.employee_id,"not_generated") for e in snapshot.employees.list()},
        critical_catalog_gaps=uncovered,revision=snapshot.revision,as_of_date=as_of_date)
