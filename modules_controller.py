
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# Simulación de base de datos de módulos dormidos (esto luego puede venir de un archivo o sistema real)
dormant_modules = {
    "deepseek_editor": False,
    "macro_events": False,
    "emotion_engine": False,
    "compliance_monitor": False,
    "ai_market_maker": False,
    "ai_macro_event_analysis": False,
    "darkpool_orchestrator": False,
    "neuralink_bridge": False,
    "quantum_trading": False,
    "god_mode_terminal": False
}

@router.get("/api/modules/dormant")
async def list_dormant_modules():
    return {"modules": [{"module": k, "active": v} for k, v in dormant_modules.items()]}

@router.post("/api/modules/activate")
async def activate_module(request: Request):
    body = await request.json()
    module_name = body.get("module")
    if module_name in dormant_modules:
        dormant_modules[module_name] = True
        return {"status": "activated", "module": module_name}
    return JSONResponse(status_code=404, content={"error": "Module not found"})
