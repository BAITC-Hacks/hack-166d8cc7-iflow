from datetime import date
from .recommendation import RecommendationCandidate
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
    candidates: list[RecommendationCandidate]
    revision: int
    as_of_date: date

from .employee import Employee

class EmployeeSummary(Model):
    employee_id: str
    full_name: str
    role: str
    grade: str

class EmployeeList(Model):
    items: list[EmployeeSummary]
    revision: int
    as_of_date: date

class EmployeeDetail(Model):
    profile: Employee
    current_skills: dict[str,int]
    history: list[ParticipationView]
    revision: int
    as_of_date: date

from uuid import UUID

class SkillChange(Model):
    skill_id: str
    before: int
    after: int
    gain: int

class CompletionResult(Model):
    command_id: UUID
    employee_id: str
    event_id: str
    skill_changes: list[SkillChange]
    trajectory: Trajectory
    revision: int
    as_of_date: date

class CompletionCommand(Model):
    command_id: UUID
    source_record_id: str | None = None
    session_date: date | None = None

class ImportResult(Model):
    added_employees: int
    unchanged_employees: int
    added_history: int
    unchanged_history: int
    revision: int
    as_of_date: date

from typing import Literal

class SkillGapCount(Model):
    skill_id: str
    name: str
    employee_count: int

class ParticipationCount(Model):
    event_id: str
    title: str
    status_counts: dict[str,int]

class HRDashboard(Model):
    skill_gap_counts: list[SkillGapCount]
    participation_by_event: list[ParticipationCount]
    employees_without_candidate: list[str]
    recommendation_status: Literal["not_implemented"]
    employees_without_recommendation: None
    revision: int
    as_of_date: date
