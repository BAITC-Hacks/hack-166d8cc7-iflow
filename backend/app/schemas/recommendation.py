from datetime import date
from typing import Literal
from .common import Model

FactorKind = Literal["current_grade","target_grade","skill_levels","critical_skill","attainable_gain","completed_history","participation_outcomes","availability","duration_format"]
class RecommendationFactor(Model):
    kind: FactorKind
    values: dict[str, str | int | float | bool | None]
    source_ids: list[str]

class EligibilityResult(Model):
    eligible: bool
    reasons: list[str]
    next_session: date | None

class RecommendationCandidate(Model):
    event_id: str
    title: str
    possible_skill_gains: dict[str,int]
    eligibility: EligibilityResult
    factors: list[RecommendationFactor]
    score: float | None = None

from pydantic import Field

class RecommendationItem(Model):
    event_id: str
    explanation: str = Field(min_length=1)
    evidence: list[RecommendationFactor]

class RecommendationResult(Model):
    status: Literal["success","no_candidates"]
    employee_id: str
    recommendations: list[RecommendationItem]
    revision: int
    as_of_date: date
