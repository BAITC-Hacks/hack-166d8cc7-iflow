from datetime import date
from app.repositories.dataset import DatasetSnapshot
from app.schemas.common import GRADES
from app.schemas.responses import Trajectory, TargetAnalysis
from .progress_engine import current_skills, effective_history
from .skill_gap import analyze_target

def targets_for(employee,current,snapshot: DatasetSnapshot) -> tuple[TargetAnalysis | None,TargetAnalysis | None]:
    i=GRADES.index(employee.grade)
    nxt=analyze_target(current,snapshot.skills.role_profile(employee.role,GRADES[i+1]),snapshot.skills) if i<3 else None
    goal=employee.career_goal
    target=analyze_target(current,snapshot.skills.role_profile(goal.target_role,goal.target_grade),snapshot.skills) if goal else None
    return nxt,target

def build_trajectory(employee_id: str,snapshot: DatasetSnapshot,as_of_date: date) -> Trajectory:
    employee=snapshot.employees.get(employee_id)
    if employee is None: raise LookupError("Employee not found")
    history=effective_history(snapshot,employee_id)
    current=current_skills(snapshot,employee_id,as_of_date)
    nxt,goal=targets_for(employee,current,snapshot)
    from .eligibility import evaluate_event
    targets=[t for t in (nxt,goal) if t is not None]
    candidates=[evaluate_event(employee,current,targets,history,event,as_of_date) for event in snapshot.events.list()]
    return Trajectory(employee_id=employee_id,next_grade=nxt.grade if nxt else None,
        next_grade_gaps=nxt.gaps if nxt else [],career_goal_analysis=goal,
        requirement_coverage=nxt.requirement_coverage if nxt else None,
        completed_activities=[r for r in history if r.status=="completed"],
        candidates=[c for c in candidates if c.eligibility.eligible],revision=snapshot.revision,as_of_date=as_of_date)
