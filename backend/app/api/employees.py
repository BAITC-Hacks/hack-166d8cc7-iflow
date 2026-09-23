from fastapi import APIRouter, Depends
from .dependencies import RequestContext, context, employee_read_context
from app.schemas.responses import EmployeeList, EmployeeSummary, EmployeeDetail, Trajectory
from app.services.progress_engine import current_skills, effective_history
from app.services.trajectory import build_trajectory

router=APIRouter(prefix="/api/employees",tags=["employees"])

@router.get("",response_model=EmployeeList)
def list_employees(ctx: RequestContext=Depends(context)):
    rows=ctx.snapshot.employees.list()
    if ctx.principal.role=="employee": rows=tuple(r for r in rows if r.employee_id==ctx.principal.employee_id)
    return EmployeeList(items=[EmployeeSummary(employee_id=r.employee_id,full_name=r.full_name,role=r.role,grade=r.grade) for r in rows],
                        revision=ctx.snapshot.revision,as_of_date=ctx.as_of_date)

@router.get("/{employee_id}",response_model=EmployeeDetail)
def employee(employee_id: str,ctx: RequestContext=Depends(employee_read_context)):
    profile=ctx.snapshot.employees.get(employee_id)
    history=effective_history(ctx.snapshot,employee_id)
    return EmployeeDetail(profile=profile,current_skills=current_skills(ctx.snapshot,employee_id,ctx.as_of_date),
                          history=history,revision=ctx.snapshot.revision,as_of_date=ctx.as_of_date)

@router.get("/{employee_id}/trajectory",response_model=Trajectory)
def trajectory(employee_id: str,ctx: RequestContext=Depends(employee_read_context)):
    return build_trajectory(employee_id,ctx.snapshot,ctx.as_of_date)
