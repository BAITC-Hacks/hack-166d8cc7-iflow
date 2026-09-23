from typing import Literal, Protocol
from datetime import date
from app.schemas.common import Model
from app.schemas.employee import Employee
from app.schemas.activity import Event
from app.schemas.history import ParticipationView
from app.schemas.skill import RoleProfile, Skill
from app.schemas.responses import TargetAnalysis
from app.schemas.recommendation import RecommendationCandidate, RecommendationResult, RecommendationFactor


class HistoryContext(Model):
    participation: ParticipationView
    event: Event
    completion_date_basis: Literal["not_completed", "historical_date_proxy", "runtime_recorded"]
    included_in_skill_projection: bool


class RoleRequirementContext(Model):
    purpose: Literal["current_role", "next_grade_benchmark", "explicit_career_goal"]
    profile: RoleProfile
    analysis: TargetAnalysis


class UnknownPreference(Model):
    key: str
    reason: str
    suggested_question: str


class ExcludedEvent(Model):
    event_id: str
    reasons: list[str]

class AIRefinementInput(Model):
    employee_id: str
    current_grade: str
    employee: Employee
    current_skills: dict[str, int]
    skill_catalog: list[Skill]
    proficiency_scale: dict[str, str]
    history: list[HistoryContext]
    event_catalog: list[Event]
    role_requirements: list[RoleRequirementContext]
    targets: list[TargetAnalysis]
    candidates: list[RecommendationCandidate]
    excluded_events: list[ExcludedEvent]
    facts: list[RecommendationFactor]
    unknown_preferences: list[UnknownPreference]
    revision: int
    as_of_date: date

class AIClient(Protocol):
    def refine(self,context: AIRefinementInput) -> RecommendationResult: ...
