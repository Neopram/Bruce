from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bruce_api import emotion, memory, inference, rlhf, tia

app = FastAPI(
    title="Bruce AI - Symbolic Backend",
    description="The backbone of Bruce's consciousness. Modular. Strategic. Symbiotic.",
    version="1.0.0"
)

# Middleware: allow communication from frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (symbolic modules)
app.include_router(emotion.router, prefix="/api/emotion", tags=["Emotion"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(inference.router, prefix="/api/infer", tags=["Inference"])
app.include_router(rlhf.router, prefix="/api/rlhf", tags=["Reinforcement Learning"])
app.include_router(tia.router, prefix="/api/tia", tags=["Task Intelligence"])


@app.get("/")
def read_root():
    return {
        "message": "Bruce AI symbolic backend is online.",
        "status": "ready",
        "version": "1.0.0",
        "modules": ["emotion", "memory", "inference", "rlhf", "tia"],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "bruce_api",
        "version": "1.0.0",
    }
