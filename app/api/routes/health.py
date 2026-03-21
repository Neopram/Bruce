from fastapi import APIRouter
import psutil

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    }