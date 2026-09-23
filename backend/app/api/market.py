from fastapi import APIRouter, Depends, Request

from app.api.dependencies import RequestContext, context
from app.schemas.market import MarketState, Redemption, RedemptionCommand


router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("", response_model=MarketState)
def market(request: Request, ctx: RequestContext = Depends(context)):
    return request.app.state.market.read(ctx.principal, ctx.as_of_date)


@router.post("/redeem", response_model=Redemption)
def redeem(command: RedemptionCommand, request: Request, ctx: RequestContext = Depends(context)):
    return request.app.state.market.redeem(ctx.principal, command, ctx.as_of_date)
