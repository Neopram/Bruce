
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ai_core.self_auditor import BruceSelfAuditor
from ai_core.feedback_collector import FeedbackCollector
from ai_core.bruce_evolver import BruceEvolver
from ai_core.personality_engine import PersonalityEngine

router_extensions = APIRouter()

# === 🧠 Self Audit ===
@router_extensions.get("/self-audit")
async def run_self_audit():
    auditor = BruceSelfAuditor(base_path=".")
    result = auditor.analyze()
    return JSONResponse(content=result)

# === 📥 Feedback Collector ===
@router_extensions.post("/feedback/save")
async def save_feedback(request: Request):
    body = await request.json()
    prompt = body.get("prompt")
    reply = body.get("reply")
    quality = body.get("quality", "neutral")
    model = body.get("model", "deepseek")
    notes = body.get("notes", "")
    FeedbackCollector().save_feedback(prompt, reply, quality, model, notes)
    return {"status": "saved"}

@router_extensions.get("/feedback/stats")
async def feedback_stats():
    stats = FeedbackCollector().get_feedback_stats()
    return stats

# === 🌱 Evolve Kernel ===
@router_extensions.post("/evolve")
async def evolve_kernel():
    evolver = BruceEvolver()
    outcome = evolver.evolve()
    return JSONResponse(content=outcome)

# === 🎭 Personality Control ===
@router_extensions.get("/personality/describe")
async def describe_personality():
    return PersonalityEngine().describe_personality()

@router_extensions.post("/personality/update")
async def update_personality(request: Request):
    body = await request.json()
    new_profile = PersonalityEngine().update_profile(**body)
    return JSONResponse(content=new_profile)
