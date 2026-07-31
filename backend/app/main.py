import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import db
from app.core.redis import redis_client

from app.api import auth, rooms, execution, analytics
from app.websocket import collab_ws, presence_ws, ai_ws

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nexagrid.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NexaGrid Backend Platform...")
    await db.connect()
    await redis_client.connect()
    yield
    logger.info("Shutting down NexaGrid Backend Platform...")
    await db.close()
    await redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for local dev & production clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(rooms.router, prefix=settings.API_PREFIX)
app.include_router(execution.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)

# Register WebSocket Handlers
app.include_router(collab_ws.router)
app.include_router(presence_ws.router)
app.include_router(ai_ws.router)

# Mount Prometheus Exporter Metrics Endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "NexaGrid API Gateway",
        "version": settings.VERSION,
        "database": "connected" if db.pool or db.use_sqlite else "disconnected",
        "redis": "connected" if redis_client.redis or redis_client.use_fallback else "fallback"
    }

@app.get("/")
async def root():
    return {"message": "Welcome to NexaGrid - Real-Time Collaborative Code Platform API"}
