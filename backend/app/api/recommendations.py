from fastapi import APIRouter, Depends, Request
from .dependencies import RequestContext, employee_read_context
from app.schemas.recommendation import RecommendationResult
from app.services.recommendation_engine import recommend
from app.ai.client import AIRefinementInput
from app.services.recommendation_context import build_recommendation_context

router=APIRouter(prefix="/api/employees",tags=["recommendations"])
@router.post("/{employee_id}/recommendations",response_model=RecommendationResult)
def recommendations(employee_id: str,request: Request,ctx: RequestContext=Depends(employee_read_context)):
    return request.app.state.notifications.generate(employee_id)


@router.get("/{employee_id}/recommendations/context", response_model=AIRefinementInput)
def recommendation_context(employee_id: str, ctx: RequestContext=Depends(employee_read_context)):
    return build_recommendation_context(employee_id, ctx.snapshot, ctx.as_of_date)
