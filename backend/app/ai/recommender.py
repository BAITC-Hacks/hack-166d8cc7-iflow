from app.core.errors import DomainError
from app.schemas.recommendation import RecommendationResult
from .client import AIRefinementInput
from collections.abc import Callable
from .prompts import build_recommendation_messages


class JSONRecommender:
    """Adapt a provider's JSON text completion callable to the typed AI boundary."""
    def __init__(self, complete: Callable[[list[dict[str, str]]], str]):
        self.complete = complete

    def refine(self, context: AIRefinementInput) -> RecommendationResult:
        result = RecommendationResult.model_validate_json(self.complete(build_recommendation_messages(context)))
        return validate_recommendation_result(context, result)

class DisabledRecommender:
    def refine(self,context: AIRefinementInput) -> RecommendationResult:
        raise DomainError("recommendations_not_implemented","An AI provider is not configured")

def validate_recommendation_result(context: AIRefinementInput,result: RecommendationResult) -> RecommendationResult:
    if (result.employee_id,result.revision,result.as_of_date)!=(context.employee_id,context.revision,context.as_of_date):
        raise ValueError("Recommendation context is stale or mismatched")
    allowed={c.event_id:c for c in context.candidates if c.eligibility.eligible}
    all_facts=context.facts+[f for candidate in context.candidates for f in candidate.factors]
    for hypothesis in result.hypotheses:
        if any(f not in all_facts for f in hypothesis.evidence):
            raise ValueError("Hypothesis evidence is not supported by context")
    if any(not question.strip() for question in result.clarifying_questions):
        raise ValueError("Clarifying questions must not be empty")
    if result.status=="no_candidates":
        if allowed or result.recommendations: raise ValueError("Candidates exist")
        return result
    if result.status == "needs_clarification":
        if result.recommendations or not result.clarifying_questions:
            raise ValueError("Uncertain primary choice requires questions and no recommendations")
        return result
    if not 1<=len(result.recommendations)<=3: raise ValueError("Expected one to three recommendations")
    seen=set()
    for item in result.recommendations:
        if item.event_id not in allowed or item.event_id in seen: raise ValueError("Unknown or duplicate activity")
        seen.add(item.event_id)
        if len({f.kind for f in item.evidence})<3: raise ValueError("At least three distinct factors required")
        candidate_facts=allowed[item.event_id].factors
        if any(f not in candidate_facts+context.facts for f in item.evidence):
            raise ValueError("Evidence is not supported by deterministic facts")
        if not any(f in candidate_facts and f.kind in {"skill_levels","critical_skill","attainable_gain"} for f in item.evidence):
            raise ValueError("Recommendation must explain a candidate's skill relevance")
    if result.recommendations[0].confidence == "uncertain":
        if not result.clarifying_questions:
            raise ValueError("Uncertain primary choice requires clarifying questions")
        return result.model_copy(update={"status": "needs_clarification", "recommendations": []})
    # Conservative server gate: uncertainty or missing marginal benefit never
    # turns into extra nodes on the map or extra offers in the mail queue.
    if any(item.confidence != "high" or not (item.additional_value or "").strip()
           for item in result.recommendations[1:]):
        return result.model_copy(update={"recommendations": result.recommendations[:1]})
    return result
