from typing import Protocol
from datetime import date
from app.schemas.common import Model
from app.schemas.responses import TargetAnalysis
from app.schemas.recommendation import RecommendationCandidate, RecommendationResult

class AIRefinementInput(Model):
    employee_id: str
    current_grade: str
    targets: list[TargetAnalysis]
    candidates: list[RecommendationCandidate]
    revision: int
    as_of_date: date

class AIClient(Protocol):
    def refine(self,context: AIRefinementInput) -> RecommendationResult: ...
