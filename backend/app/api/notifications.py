from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import RequestContext, employee_read_context, hr_context
from app.core.auth import require_self
from app.schemas.notifications import (
    EmployeeNotificationPreferences, HRContactUpdate, NotificationSettings,
    OfferAction, ResolveDelivery, SMTPConnection, TestMailCommand,
)

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/hr/notifications/settings")
def settings(request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.settings_view()


@router.post("/hr/notifications/settings")
def save_settings(value: NotificationSettings, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.update_settings(value)


@router.post("/hr/notifications/mail-account")
def connect(value: SMTPConnection, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.connect(value)


@router.post("/hr/notifications/mail-account/disconnect")
def disconnect(request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.disconnect()


@router.post("/hr/notifications/test")
def test_mail(value: TestMailCommand, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.queue_test(value)


@router.get("/hr/notifications/preview/{employee_id}")
def preview(employee_id: str, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.preview(employee_id)


@router.get("/hr/notifications/journal")
def journal(request: Request, employee_id: str | None = None, after: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=500), ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.journal_view(employee_id, after, limit)


@router.post("/hr/notifications/deliveries/{delivery_id}/resolve")
def resolve(delivery_id: str, value: ResolveDelivery, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.resolve_unknown(delivery_id, value)


@router.post("/hr/notifications/deliveries/{delivery_id}/retry")
def retry(delivery_id: str, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.retry_failed(delivery_id)


@router.post("/hr/notifications/contacts/{employee_id}")
def contact(employee_id: str, value: HRContactUpdate, request: Request, ctx: RequestContext = Depends(hr_context)):
    return request.app.state.notifications.update_preferences(employee_id, hr_update=value)


@router.get("/employees/{employee_id}/notifications")
def employee_notifications(employee_id: str, request: Request, ctx: RequestContext = Depends(employee_read_context)):
    return request.app.state.notifications.offers_view(employee_id)


@router.post("/employees/{employee_id}/notifications/preferences")
def preferences(employee_id: str, value: EmployeeNotificationPreferences, request: Request,
                ctx: RequestContext = Depends(employee_read_context)):
    require_self(ctx.principal, employee_id)
    return request.app.state.notifications.update_preferences(employee_id, preferences=value)


@router.post("/employees/{employee_id}/offers/{offer_id}/actions")
def action(employee_id: str, offer_id: str, value: OfferAction, request: Request,
           ctx: RequestContext = Depends(employee_read_context)):
    require_self(ctx.principal, employee_id)
    return request.app.state.notifications.action(employee_id, offer_id, value)
