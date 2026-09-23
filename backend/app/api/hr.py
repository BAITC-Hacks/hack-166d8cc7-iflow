from fastapi import APIRouter, Depends
from .dependencies import RequestContext, hr_context
from app.schemas.responses import HRDashboard
from app.services.hr import build_hr_dashboard

router=APIRouter(prefix="/api/hr",tags=["hr"])
@router.get("/dashboard",response_model=HRDashboard)
def dashboard(ctx: RequestContext=Depends(hr_context)):
    return build_hr_dashboard(ctx.snapshot,ctx.as_of_date)
