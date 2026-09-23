from fastapi import APIRouter, Depends

from app.api.dependencies import RequestContext, context
from app.core.auth import Principal


router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("", response_model=Principal)
def session(ctx: RequestContext = Depends(context)):
    return ctx.principal
