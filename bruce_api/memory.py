# Memory module for reflection and symbolic storage

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from bruce_api.utils import success_response, error_response, utc_now

router = APIRouter()

# ─── In-memory storage (mirrors MemoryManager pattern) ───────────────

_memory_store: Dict[str, List[Dict[str, Any]]] = {}
_search_index: Dict[str, List[Dict[str, Any]]] = {}  # tag-based index


# ─── Pydantic Models ────────────────────────────────────────────────

class MemoryStoreRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User identifier")
    content: str = Field(..., min_length=1, description="Memory content to store")
    category: str = Field("general", description="Memory category (e.g., decision, reflection, interaction)")
    tags: List[str] = Field(default_factory=list, description="Tags for search and retrieval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MemoryRecallRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User identifier")
    limit: int = Field(10, ge=1, le=100, description="Maximum memories to return")
    category: Optional[str] = Field(None, description="Filter by category")


class MemorySearchRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User identifier")
    query: str = Field(..., min_length=1, description="Search query text")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")


class MemoryEntry(BaseModel):
    id: int
    user_id: str
    content: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    timestamp: str


# ─── Endpoints ───────────────────────────────────────────────────────

@router.post("/store")
async def store_memory(request: MemoryStoreRequest):
    """Store a new memory entry for a user."""
    user_memories = _memory_store.setdefault(request.user_id, [])

    entry = {
        "id": len(user_memories) + 1,
        "user_id": request.user_id,
        "content": request.content,
        "category": request.category,
        "tags": request.tags,
        "metadata": request.metadata,
        "timestamp": utc_now(),
    }

    user_memories.append(entry)

    # Update search index by tags
    for tag in request.tags:
        _search_index.setdefault(tag, []).append(entry)

    return success_response(
        data=entry,
        message=f"Memory stored for user '{request.user_id}'.",
    )


@router.post("/recall")
async def recall_memories(request: MemoryRecallRequest):
    """Recall recent memories for a user, optionally filtered by category."""
    user_memories = _memory_store.get(request.user_id, [])

    if request.category:
        user_memories = [m for m in user_memories if m["category"] == request.category]

    # Return most recent entries
    recent = user_memories[-request.limit:]
    recent.reverse()

    return success_response(
        data=recent,
        message=f"Recalled {len(recent)} memories for user '{request.user_id}'.",
    )


@router.post("/search")
async def search_memories(request: MemorySearchRequest):
    """Search memories by query text and/or tags."""
    user_memories = _memory_store.get(request.user_id, [])

    if not user_memories:
        return success_response(data=[], message="No memories found for this user.")

    results = []
    query_lower = request.query.lower()

    for mem in user_memories:
        # Text match
        text_match = query_lower in mem["content"].lower()

        # Tag match
        tag_match = False
        if request.tags:
            tag_match = any(t in mem["tags"] for t in request.tags)

        if text_match or tag_match:
            results.append(mem)

    results = results[-request.limit:]
    results.reverse()

    return success_response(
        data=results,
        message=f"Found {len(results)} matching memories.",
    )


@router.delete("/{user_id}")
async def clear_user_memories(user_id: str):
    """Delete all memories for a specific user."""
    if user_id not in _memory_store:
        raise HTTPException(status_code=404, detail=f"No memories found for user '{user_id}'")

    count = len(_memory_store[user_id])
    del _memory_store[user_id]

    # Clean search index
    for tag in list(_search_index.keys()):
        _search_index[tag] = [e for e in _search_index[tag] if e["user_id"] != user_id]
        if not _search_index[tag]:
            del _search_index[tag]

    return success_response(
        data={"deleted_count": count},
        message=f"Cleared {count} memories for user '{user_id}'.",
    )


@router.get("/stats")
async def memory_stats():
    """Get global memory statistics."""
    total_memories = sum(len(v) for v in _memory_store.values())
    users_with_memories = len(_memory_store)

    categories: Dict[str, int] = {}
    for user_mems in _memory_store.values():
        for mem in user_mems:
            cat = mem["category"]
            categories[cat] = categories.get(cat, 0) + 1

    return success_response(
        data={
            "total_memories": total_memories,
            "users_with_memories": users_with_memories,
            "categories": categories,
            "unique_tags": len(_search_index),
        },
        message="Memory statistics retrieved.",
    )
