from datetime import date
from typing import Any
from .common import Model
from .history import ParticipationView

class SkillGap(Model):
    skill_id: str
    name: str
    current_level: int
    required_level: int
    gap: int
    is_critical: bool

class TargetAnalysis(Model):
    role: str
    grade: str
    gaps: list[SkillGap]
    requirement_coverage: float

class Trajectory(Model):
    employee_id: str
    next_grade: str | None
    next_grade_gaps: list[SkillGap]
    career_goal_analysis: TargetAnalysis | None
    requirement_coverage: float | None
    completed_activities: list[ParticipationView]
    candidates: list[Any]
    revision: int
    as_of_date: date
