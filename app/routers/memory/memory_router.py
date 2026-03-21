from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/memory", tags=["memory"])

# ─── In-memory store (wraps MemoryManager pattern) ───────────────────

_store: Dict[str, List[Dict[str, Any]]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic Models ────────────────────────────────────────────────

class MemoryStoreRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Content to remember")
    category: str = Field("general", description="Memory category")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    tags: List[str] = Field(default_factory=list)
    limit: int = Field(10, ge=1, le=100)


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
def memory_root(user: dict = Depends(get_current_user)):
    return {"message": "Memory module active", "user": user.get("sub")}


@router.post("/store")
async def store_memory(request: MemoryStoreRequest, user: dict = Depends(get_current_user)):
    """Store a new memory entry for the authenticated user."""
    user_id = user.get("sub", "anonymous")
    entries = _store.setdefault(user_id, [])

    entry = {
        "id": len(entries) + 1,
        "content": request.content,
        "category": request.category,
        "tags": request.tags,
        "metadata": request.metadata,
        "timestamp": _utc_now(),
    }
    entries.append(entry)

    return {"success": True, "data": entry, "message": "Memory stored."}


@router.get("/recall/{user_id}")
async def recall_memories(
    user_id: str,
    limit: int = 10,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Recall recent memories for a user."""
    entries = _store.get(user_id, [])

    if category:
        entries = [e for e in entries if e["category"] == category]

    recent = entries[-limit:]
    recent.reverse()

    return {
        "user_id": user_id,
        "memories": recent,
        "total": len(_store.get(user_id, [])),
        "returned": len(recent),
    }


@router.post("/search")
async def search_memories(request: MemorySearchRequest, user: dict = Depends(get_current_user)):
    """Search memories by text query and/or tags."""
    user_id = user.get("sub", "anonymous")
    entries = _store.get(user_id, [])

    results = []
    query_lower = request.query.lower()

    for entry in entries:
        text_match = query_lower in entry["content"].lower()
        tag_match = any(t in entry["tags"] for t in request.tags) if request.tags else False

        if text_match or tag_match:
            results.append(entry)

    results = results[-request.limit:]
    results.reverse()

    return {"results": results, "total_matches": len(results)}


@router.delete("/clear/{user_id}")
async def clear_memories(user_id: str, user: dict = Depends(get_current_user)):
    """Clear all memories for a user."""
    if user_id not in _store:
        raise HTTPException(status_code=404, detail=f"No memories for user '{user_id}'")

    count = len(_store[user_id])
    del _store[user_id]

    return {"success": True, "cleared": count, "message": f"Cleared {count} memories."}


@router.get("/stats")
async def memory_stats(user: dict = Depends(get_current_user)):
    """Get memory statistics."""
    total = sum(len(v) for v in _store.values())
    users = len(_store)

    categories: Dict[str, int] = {}
    for entries in _store.values():
        for e in entries:
            cat = e["category"]
            categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_memories": total,
        "users_tracked": users,
        "categories": categories,
    }
