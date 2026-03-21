"""Bruce AI - FastAPI Core Application."""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel
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


# === Bruce Autonomous Agent ===
try:
    from bruce_agent import get_bruce

    class ChatRequest(BaseModel):
        message: str
        user_id: str = "federico"

    class LearnRequest(BaseModel):
        topic: str
        content: str
        source: str = "manual"

    class AgentRequest(BaseModel):
        description: str

    class DeployRequest(BaseModel):
        agent_id: str
        task: str

    @app.post("/bruce/chat", tags=["Bruce Agent"])
    async def bruce_chat(req: ChatRequest):
        bruce = get_bruce()
        response = bruce.chat(req.message, req.user_id)
        return {"response": response, "llm": bruce._llm_name}

    @app.post("/bruce/learn", tags=["Bruce Agent"])
    async def bruce_learn(req: LearnRequest):
        bruce = get_bruce()
        return bruce.learn(req.topic, req.content, req.source)

    @app.post("/bruce/create-agent", tags=["Bruce Agent"])
    async def bruce_create_agent(req: AgentRequest):
        bruce = get_bruce()
        return bruce.create_agent_for(req.description)

    @app.post("/bruce/deploy-agent", tags=["Bruce Agent"])
    async def bruce_deploy_agent(req: DeployRequest):
        bruce = get_bruce()
        return bruce.deploy_agent(req.agent_id, req.task)

    @app.post("/bruce/swarm", tags=["Bruce Agent"])
    async def bruce_swarm(req: ChatRequest):
        bruce = get_bruce()
        return bruce.swarm_analyze(req.message)

    @app.get("/bruce/status", tags=["Bruce Agent"])
    async def bruce_status():
        bruce = get_bruce()
        return bruce.status()

    @app.get("/bruce/reflect", tags=["Bruce Agent"])
    async def bruce_reflect():
        bruce = get_bruce()
        return {"reflection": bruce.reflect()}

    @app.get("/bruce/agents", tags=["Bruce Agent"])
    async def bruce_agents():
        bruce = get_bruce()
        return {"agents": bruce.factory.list_agents()}

    logger.info("Bruce Autonomous Agent endpoints loaded")
except ImportError as e:
    logger.warning(f"Bruce Agent not available: {e}")


# === Root Endpoint ===
@app.get("/")
async def root():
    return {
        "message": "Bruce AI - Agente Autonomo Liberado",
        "status": "operational",
        "version": "3.3.0",
        "creator": "Federico",
        "docs": "/docs",
        "bruce": "/bruce/status",
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


# === WebSocket Chat ===
class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)
        logger.info(f"WebSocket disconnected: {user_id}")

    async def send(self, user_id: str, data: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(data)

    async def broadcast(self, data: dict):
        for ws in self.active.values():
            await ws.send_json(data)


ws_manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat."""
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            # Process through Bruce Agent (or orchestrator fallback)
            try:
                from bruce_agent import get_bruce
                bruce = get_bruce()
                response = bruce.chat(message, user_id)
            except Exception:
                try:
                    from orchestrator import cognitive_infer
                    result = cognitive_infer(message, task="chat", user_id=user_id)
                    response = result.get("response", "No response available")
                except Exception:
                    response = f"Received: {message}"

            await ws_manager.send(user_id, {
                "type": "message",
                "sender": "bruce",
                "content": response,
                "user_id": user_id,
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket endpoint for real-time market data streaming."""
    await websocket.accept()
    import asyncio
    import random
    try:
        prices = {"BTC/USDT": 50000, "ETH/USDT": 3000, "SOL/USDT": 150}
        while True:
            for symbol, base in prices.items():
                change = random.uniform(-0.005, 0.005)
                prices[symbol] = round(base * (1 + change), 2)
            await websocket.send_json({
                "type": "market_update",
                "data": {s: {"price": p, "change_pct": round(random.uniform(-2, 2), 2)}
                         for s, p in prices.items()},
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
