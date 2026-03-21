from .chat.chat_router import router as chat_router
from .feedback.feedback_router import router as feedback_router
from .memory.memory_router import router as memory_router
from .profile.profile_router import router as profile_router
from .narrador.narrador_router import router as narrador_router

__all__ = [
    "chat_router",
    "feedback_router",
    "memory_router",
    "profile_router",
    "narrador_router"
]
