from fastapi import APIRouter, Depends
from .dependencies import RequestContext, employee_read_context
from app.schemas.recommendation import RecommendationResult
from app.services.recommendation_engine import recommend

router=APIRouter(prefix="/api/employees",tags=["recommendations"])
@router.post("/{employee_id}/recommendations",response_model=RecommendationResult)
def recommendations(employee_id: str,ctx: RequestContext=Depends(employee_read_context)):
    return recommend(employee_id,ctx.snapshot,ctx.as_of_date)
