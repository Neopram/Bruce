from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# ─── In-memory conversation store ────────────────────────────────────

_conversations: Dict[str, List[Dict[str, Any]]] = {}


# ─── Pydantic Models ────────────────────────────────────────────────

class ChatSendRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message to send to Bruce")
    lang: str = Field("en", description="Language code")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    user_message: str
    bruce_response: str
    conversation_id: str
    timestamp: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
async def chat_root(user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome to the chat module, {user.get('sub', 'user')}.",
        "role": user.get("role", "unknown"),
    }


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatSendRequest, user: dict = Depends(get_current_user)):
    """
    Send a message and get a response from Bruce.
    Attempts to use the inference engine; falls back to echo-style response.
    """
    user_id = user.get("sub", "anonymous")
    now = _utc_now()

    # Store user message
    history = _conversations.setdefault(user_id, [])
    history.append({
        "role": "user",
        "content": request.message,
        "timestamp": now,
        "metadata": request.context,
    })

    # Generate response via orchestrator / inference
    try:
        from ai_core.infer_router import infer_from_bruce
        bruce_reply = await infer_from_bruce(request.message, lang=request.lang)
    except Exception:
        bruce_reply = (
            f"[Bruce] I received your message: '{request.message[:120]}'. "
            "My inference engine is currently warming up. I'll respond more precisely soon."
        )

    # Store assistant response
    history.append({
        "role": "assistant",
        "content": bruce_reply,
        "timestamp": _utc_now(),
        "metadata": {},
    })

    # Cap history at 200 messages per user
    if len(history) > 200:
        _conversations[user_id] = history[-200:]

    return ChatResponse(
        user_message=request.message,
        bruce_response=bruce_reply,
        conversation_id=user_id,
        timestamp=now,
    )


@router.get("/history/{user_id}")
async def get_conversation_history(
    user_id: str,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """Retrieve conversation history for a user."""
    history = _conversations.get(user_id, [])

    if not history:
        return {
            "user_id": user_id,
            "messages": [],
            "total": 0,
            "message": "No conversation history found.",
        }

    recent = history[-limit:]

    return {
        "user_id": user_id,
        "messages": recent,
        "total": len(history),
        "returned": len(recent),
    }


@router.post("/clear/{user_id}")
async def clear_conversation(user_id: str, user: dict = Depends(get_current_user)):
    """Clear conversation history for a user."""
    if user_id not in _conversations:
        raise HTTPException(status_code=404, detail=f"No conversation found for user '{user_id}'")

    count = len(_conversations[user_id])
    del _conversations[user_id]

    return {
        "success": True,
        "user_id": user_id,
        "cleared_messages": count,
        "message": f"Conversation cleared ({count} messages removed).",
    }


@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat with Bruce.
    Accepts text messages and returns Bruce's responses.
    """
    await websocket.accept()

    history = _conversations.setdefault(user_id, [])

    try:
        while True:
            data = await websocket.receive_text()

            # Store user message
            history.append({
                "role": "user",
                "content": data,
                "timestamp": _utc_now(),
                "metadata": {"source": "websocket"},
            })

            # Generate response
            try:
                from ai_core.infer_router import infer_from_bruce
                reply = await infer_from_bruce(data)
            except Exception:
                reply = f"[Bruce WS] Received: {data[:100]}"

            history.append({
                "role": "assistant",
                "content": reply,
                "timestamp": _utc_now(),
                "metadata": {"source": "websocket"},
            })

            await websocket.send_text(reply)

    except WebSocketDisconnect:
        pass
