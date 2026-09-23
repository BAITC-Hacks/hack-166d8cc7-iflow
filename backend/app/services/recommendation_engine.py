from datetime import date
from app.core.errors import DomainError
from app.repositories.dataset import DatasetSnapshot
from app.schemas.recommendation import RecommendationResult
from app.ai.client import AIClient
from app.ai.recommender import DisabledRecommender, validate_recommendation_result
from .recommendation_context import build_recommendation_context

def recommend(employee_id: str,snapshot: DatasetSnapshot,as_of_date: date,
              ai_client: AIClient | None = None) -> RecommendationResult:
    context = build_recommendation_context(employee_id, snapshot, as_of_date)
    if not context.candidates:
        return RecommendationResult(status="no_candidates", employee_id=employee_id,
                                    recommendations=[], revision=context.revision, as_of_date=as_of_date)
    try:
        result = (ai_client or DisabledRecommender()).refine(context)
        return validate_recommendation_result(context, RecommendationResult.model_validate(result))
    except DomainError:
        raise
    except Exception as exc:
        raise DomainError("unavailable", "AI recommendation unavailable or returned unsupported evidence") from exc
