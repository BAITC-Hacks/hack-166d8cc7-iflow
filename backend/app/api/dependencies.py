from dataclasses import dataclass
from datetime import date
from fastapi import Depends, Request
from app.core.auth import Principal, resolve_principal, require_access, require_hr
from app.core.errors import DomainError
from app.repositories.dataset import DatasetSnapshot

@dataclass(frozen=True)
class RequestContext:
    principal: Principal
    snapshot: DatasetSnapshot
    as_of_date: date

def context(request: Request) -> RequestContext:
    p=resolve_principal(request.headers.get("authorization"),request.app.state.settings.dev_identities)
    snapshot=request.app.state.dataset.capture()
    if p.role=="employee" and snapshot.employees.get(p.employee_id) is None:
        raise DomainError("unauthorized","Employee identity no longer exists")
    return RequestContext(p,snapshot,request.app.state.as_of_date)

def employee_read_context(employee_id: str, ctx: RequestContext=Depends(context)) -> RequestContext:
    require_access(ctx.principal,employee_id)
    if ctx.snapshot.employees.get(employee_id) is None:
        raise DomainError("not_found","Employee not found")
    return ctx

def hr_context(ctx: RequestContext=Depends(context)) -> RequestContext:
    require_hr(ctx.principal)
    return ctx
