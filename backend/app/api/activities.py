from fastapi import APIRouter, Depends, Request
from app.api.dependencies import RequestContext, context
from app.schemas.responses import CompletionCommand, CompletionResult
from app.services.completion import complete_activity

router=APIRouter(prefix="/api/employees",tags=["activities"])

@router.post("/{employee_id}/activities/{event_id}/complete",response_model=CompletionResult)
def complete(employee_id: str,event_id: str,command: CompletionCommand,request: Request,ctx: RequestContext=Depends(context)):
    return complete_activity(ctx.principal,employee_id,event_id,command,request.app.state.dataset,ctx.as_of_date)
