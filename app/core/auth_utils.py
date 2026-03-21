from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()

# === 🔐 Configuración desde .env ===
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Solo para HS256
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "./infrastructure/keys/private.pem")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "./infrastructure/keys/public.pem")

# === 🔐 Instancia OAuth2 para FastAPI ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === 🔐 Carga de claves dinámicas ===
def load_private_key():
    try:
        with open(PRIVATE_KEY_PATH, "rb") as key_file:
            return serialization.load_pem_private_key(key_file.read(), password=None)
    except FileNotFoundError:
        return None

def load_public_key():
    try:
        with open(PUBLIC_KEY_PATH, "rb") as key_file:
            return serialization.load_pem_public_key(key_file.read())
    except FileNotFoundError:
        return None

private_key = load_private_key() if ALGORITHM.startswith("RS") else None
public_key = load_public_key() if ALGORITHM.startswith("RS") else None

# === 🔧 Crear token JWT (compatible HS256 / RS256) ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    if ALGORITHM.startswith("RS"):
        if not private_key:
            raise RuntimeError("Clave privada no encontrada para RS256")
        return jwt.encode(to_encode, private_key, algorithm=ALGORITHM)
    else:
        if not JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY no definido para HS256")
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

# === 🔍 Verificar token JWT (según algoritmo configurado) ===
def verify_token(token: str) -> dict:
    try:
        if ALGORITHM.startswith("RS"):
            if not public_key:
                raise RuntimeError("Clave pública no encontrada para RS256")
            payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        else:
            if not JWT_SECRET_KEY:
                raise RuntimeError("JWT_SECRET_KEY no definido para HS256")
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

# === 🧠 Obtener usuario actual desde el token JWT ===
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no identificado en el token",
        )
    return payload  # retornamos el payload completo, incluyendo role u otros claims
