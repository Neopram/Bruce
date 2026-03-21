from fastapi import APIRouter, UploadFile, File, Form
from .emotion_state import EmotionState
from .emotion_detector import detect_emotion_from_voice, detect_emotion_from_text
from .emotion_response import generate_emotional_response
from .emotion_memory import EmotionMemory

router = APIRouter(prefix="/internal/emotion", tags=["Emotion"])

emotion = EmotionState()
memory = EmotionMemory()

@router.get("/state")
def get_current_emotion():
    return emotion.get_emotion()

@router.post("/voice")
async def analyze_voice(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    result = detect_emotion_from_voice(audio_bytes)
    emotion.update_emotion(**result)
    memory.record(**result)
    return result

@router.post("/text")
async def analyze_text(text: str = Form(...)):
    result = detect_emotion_from_text(text)
    emotion.update_emotion(**result)
    memory.record(**result)
    return result

@router.get("/memory")
def get_emotional_history():
    return memory.get_last(10)

@router.get("/summary")
def summarize_emotions():
    return {"summary": memory.summarize_emotional_trajectory()}

@router.post("/response")
def respond_emotionally(text: str = Form(...)):
    return {"response": generate_emotional_response(text)}