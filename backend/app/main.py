import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import db
from app.core.redis import redis_client

# Single consolidated import block — FIX-3: removed duplicate import
from app.api import auth, rooms, execution, analytics, mcp
from app.websocket import collab_ws, presence_ws, ai_ws

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s [req_id=%(request_id)s]: %(message)s"
    if False else "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nexagrid.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NexaGrid Backend Platform v%s (%s)...", settings.VERSION, settings.ENVIRONMENT)
    await db.connect()
    await redis_client.connect()
    yield
    logger.info("Shutting down NexaGrid Backend Platform...")
    await db.close()
    await redis_client.close()


from app.core.telemetry import telemetry_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Register OpenTelemetry Distributed Tracing
telemetry_manager.instrument_fastapi(app)


# FIX-3: CORS origin allowlist from settings — no more wildcard + credentials combo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Inject a unique X-Request-ID correlation ID into every request for distributed tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Register REST Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(rooms.router, prefix=settings.API_PREFIX)
app.include_router(execution.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)
app.include_router(mcp.router, prefix=settings.API_PREFIX)

# Register WebSocket Handlers
app.include_router(collab_ws.router)
app.include_router(presence_ws.router)
app.include_router(ai_ws.router)

# Mount Prometheus Exporter — internal only in production (nginx allows /metrics from internal only)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    pool_info = {}
    if hasattr(db, "pool") and db.pool:
        pool_info = {
            "pool_size": db.pool.get_size(),
            "pool_free": db.pool.get_idle_size(),
        }
    return {
        "status": "healthy",
        "service": "NexaGrid API Gateway",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if (hasattr(db, "pool") and db.pool) or (hasattr(db, "use_sqlite") and db.use_sqlite) else "disconnected",
        "redis": "connected" if (hasattr(redis_client, "redis") and redis_client.redis) else "fallback",
        **pool_info,
    }


@app.get("/")
async def root():
    return {"message": "NexaGrid Real-Time Collaborative Code Platform", "version": settings.VERSION}
