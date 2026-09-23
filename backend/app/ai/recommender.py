from app.core.errors import DomainError
from app.schemas.recommendation import RecommendationResult
from .client import AIRefinementInput

class DisabledRecommender:
    def refine(self,context: AIRefinementInput) -> RecommendationResult:
        raise DomainError("recommendations_not_implemented","AI recommendations are not implemented")

def validate_recommendation_result(context: AIRefinementInput,result: RecommendationResult) -> RecommendationResult:
    if (result.employee_id,result.revision,result.as_of_date)!=(context.employee_id,context.revision,context.as_of_date):
        raise ValueError("Recommendation context is stale or mismatched")
    allowed={c.event_id:c for c in context.candidates if c.eligibility.eligible}
    if result.status=="no_candidates":
        if allowed or result.recommendations: raise ValueError("Candidates exist")
        return result
    if not 1<=len(result.recommendations)<=3: raise ValueError("Expected one to three recommendations")
    seen=set()
    for item in result.recommendations:
        if item.event_id not in allowed or item.event_id in seen: raise ValueError("Unknown or duplicate activity")
        seen.add(item.event_id)
        if len({f.kind for f in item.evidence})<3: raise ValueError("At least three distinct factors required")
        if any(f not in allowed[item.event_id].factors for f in item.evidence):
            raise ValueError("Evidence is not supported by deterministic facts")
    return result
