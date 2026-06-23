from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import get_settings
from tracedesk_api.database import create_engine, database_is_ready
from tracedesk_api.investigations.manager import InvestigationManager
from tracedesk_api.routers.cases import router as cases_router
from tracedesk_api.routers.evaluations import router as evaluations_router
from tracedesk_api.routers.investigations import router as investigations_router
from tracedesk_api.routers.knowledge import router as knowledge_router
from tracedesk_api.routers.sessions import router as sessions_router
from tracedesk_api.routers.tools import router as tools_router
from tracedesk_api.schemas import LiveHealth, ReadyHealth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.engine = create_engine(settings)
    app.state.investigation_manager = InvestigationManager(app.state.engine, settings)
    yield
    await app.state.investigation_manager.shutdown()
    await app.state.engine.dispose()


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Last-Event-ID"],
)
app.include_router(cases_router)
app.include_router(evaluations_router)
app.include_router(knowledge_router)
app.include_router(sessions_router)
app.include_router(tools_router)
app.include_router(investigations_router)


@app.get("/health/live", response_model=LiveHealth, tags=["health"])
async def live() -> LiveHealth:
    return LiveHealth()


@app.get(
    "/health/ready",
    response_model=ReadyHealth,
    responses={503: {"model": ReadyHealth}},
    tags=["health"],
)
async def ready(request: Request, response: Response) -> ReadyHealth:
    engine: AsyncEngine = request.app.state.engine
    try:
        await database_is_ready(engine)
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyHealth(status="not_ready", database="unavailable")
    return ReadyHealth(status="ready", database="connected")
