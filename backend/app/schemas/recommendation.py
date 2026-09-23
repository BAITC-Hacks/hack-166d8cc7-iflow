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
