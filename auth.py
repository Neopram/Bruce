"""Authentication router for Bruce AI."""

from fastapi import APIRouter, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from datetime import timedelta
from passlib.context import CryptContext

from config.settings import get_settings
from jwt_auth import create_token
from security import get_current_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In production, users should be stored in the database.
# This is a temporary in-memory store for bootstrapping.
_users_db = {}


_admin_hash_cache = {}


def _get_admin_user() -> dict:
    """Get the admin user credentials from settings."""
    settings = get_settings()
    pw = settings.admin_password
    if pw not in _admin_hash_cache:
        _admin_hash_cache[pw] = pwd_context.hash(pw)
    return {
        "username": "admin",
        "hashed_password": _admin_hash_cache[pw],
        "role": "admin",
    }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate a user by username and password."""
    admin = _get_admin_user()
    if username == admin["username"] and verify_password(password, admin["hashed_password"]):
        return admin

    user = _users_db.get(username)
    if user and verify_password(password, user["hashed_password"]):
        return user

    return None


@router.post("/token")
async def login(
    username: str = Form(...),
    password: str = Form(...),
):
    """OAuth2 password flow login endpoint."""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(user["username"], role=user.get("role", "user"))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.get("role", "user"),
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
