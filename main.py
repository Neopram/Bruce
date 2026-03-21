"""Bruce AI - FastAPI Core Application."""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings

# Ensure app/ modules are importable
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Bruce.Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Bruce AI starting in {settings.environment} mode")
    logger.info(f"Primary model: {settings.primary_model}")
    logger.info(f"Trading enabled: {settings.enable_trading}")
    yield
    logger.info("Bruce AI shutting down")


# FastAPI App
settings = get_settings()
app = FastAPI(
    title="Bruce AI Core",
    version="3.2.0",
    description="Nucleo Cognitivo de Bruce AI",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS - uses settings, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# === Route Imports ===
from auth import router as auth_router

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

try:
    from app.api.endpoints.terminal import router as terminal_router
    app.include_router(terminal_router, prefix="/api/terminal", tags=["Terminal"])
except ImportError:
    logger.warning("Terminal router not available")

try:
    from app.api.endpoints.episodes import router as episodes_router
    app.include_router(episodes_router, prefix="/api/v1", tags=["Episodes"])
except ImportError:
    logger.warning("Episodes router not available")

try:
    from app.api.endpoints.training_api import router as training_router
    app.include_router(training_router, prefix="/api/v1", tags=["RL Trainer"])
except ImportError:
    logger.warning("Training router not available")

try:
    from app.api.endpoints.deepseek_control import router as deepseek_router
    app.include_router(deepseek_router, prefix="/api", tags=["DeepSeek Supervisor"])
except ImportError:
    logger.warning("DeepSeek router not available")

try:
    from app.api.endpoints.simulation_api import router as simulation_router
    app.include_router(simulation_router, prefix="/api/v1", tags=["Simulation"])
except ImportError:
    logger.warning("Simulation router not available")

try:
    from app.api.endpoints.frontend_api import router as frontend_api_router
    app.include_router(frontend_api_router, prefix="/api", tags=["Frontend API"])
except ImportError:
    logger.warning("Frontend API router not available")


# === Root Endpoint ===
@app.get("/")
async def root():
    return {
        "message": "Bruce AI - Nucleo Cognitivo Activo",
        "status": "operational",
        "version": "3.2.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.2.0"}


# === Global Error Handler ===
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception(f"Unhandled Exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e) if settings.debug else "An unexpected error occurred",
            },
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
