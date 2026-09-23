from contextlib import asynccontextmanager
from datetime import date
import asyncio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.core.errors import DomainError, STATUS
from app.repositories.dataset import DatasetRepository, build_snapshot
from app.services.dataset import DatasetService
from app.repositories.state import StateRepository
from app.api import employees, activities, dataset, recommendations, hr, market, session
from app.services.market import MarketService
from app.ai.client import AIClient
from app.ai.openai_provider import create_recommender
from app.api import notifications
from app.services.notifications import NotificationService
from app.services.mail_transport import SMTPTransport
from app.services.notification_worker import run_worker

def create_app(settings: Settings | None = None, *, ai_client: AIClient | None = None, mailer=None, notification_clock=None) -> FastAPI:
    settings=settings or Settings.from_env()
    @asynccontextmanager
    async def lifespan(app):
        bundle=DatasetRepository(settings.raw_dir).load()
        clock=date.fromisoformat(str(settings.application_date)) if settings.application_date else bundle.meta.as_of_date
        if clock<bundle.meta.as_of_date: raise ValueError("Application date cannot precede dataset snapshot")
        app.state.dataset=DatasetService(build_snapshot(bundle),StateRepository(settings.state_path),DatasetRepository(settings.raw_dir).fingerprint())
        app.state.market=MarketService(app.state.dataset)
        app.state.settings=settings
        app.state.as_of_date=clock
        app.state.ai_client=ai_client if ai_client is not None else create_recommender(settings)
        transport = mailer or SMTPTransport(settings.mail_encryption_key.get_secret_value() if settings.mail_encryption_key else None)
        app.state.notifications = NotificationService(app.state.dataset, app.state.ai_client, transport,
            lambda: app.state.as_of_date, settings.public_app_url, now=notification_clock,
            auto_prepare=settings.ai_auto_prepare)
        app.state.notifications.recover()
        stop = asyncio.Event()
        task = asyncio.create_task(run_worker(app.state.notifications, stop, settings.notification_poll_seconds)) if settings.notifications_worker_enabled else None
        try:
            yield
        finally:
            stop.set()
            if task:
                await task
            if ai_client is None and hasattr(app.state.ai_client, "close"):
                app.state.ai_client.close()
    app=FastAPI(title="Career Quest",lifespan=lifespan)
    app.add_middleware(dataset.ImportGuard,identities=settings.dev_identities)
    app.add_middleware(CORSMiddleware,allow_origins=[settings.allowed_origin],allow_methods=["GET","POST"],
                       allow_headers=["Authorization","Content-Type"])
    @app.middleware("http")
    async def private_responses(request,call_next):
        response=await call_next(request)
        if request.url.path.startswith("/api/"): response.headers["Cache-Control"]="no-store"
        return response
    @app.exception_handler(DomainError)
    async def domain_error(request: Request,error: DomainError):
        return JSONResponse(status_code=STATUS[error.code],content={"error":{"code":error.code,"message":error.message,"details":error.details}})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request,error: RequestValidationError):
        details=[{"loc":list(e["loc"]),"type":e["type"],"message":"Invalid value"} for e in error.errors()]
        return JSONResponse(status_code=422,content={"error":{"code":"invalid","message":"Invalid request","details":details}})
    @app.get("/health")
    def health(): return {"status":"ok"}
    app.include_router(employees.router)
    app.include_router(activities.router)
    app.include_router(dataset.router)
    app.include_router(recommendations.router)
    app.include_router(hr.router)
    app.include_router(session.router)
    app.include_router(market.router)
    app.include_router(notifications.router)
    return app

app=create_app()
