from fastapi import APIRouter, Depends, Request
from .dependencies import RequestContext, hr_context
from app.schemas.responses import HRDashboard
from app.services.hr import build_hr_dashboard

router=APIRouter(prefix="/api/hr",tags=["hr"])
@router.get("/dashboard",response_model=HRDashboard)
def dashboard(request: Request, ctx: RequestContext=Depends(hr_context)):
    service = request.app.state.notifications
    with service.dataset.lock:
        snapshot = service.dataset.capture()
        states = {}
        for employee_id, record in service.state.generations.items():
            if snapshot.employees.get(employee_id) is not None:
                states[employee_id] = record.status if record.fingerprint == service._input_fingerprint(employee_id, snapshot) else "stale"
        return build_hr_dashboard(snapshot,ctx.as_of_date,states)
