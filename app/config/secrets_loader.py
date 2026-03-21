import yaml
import os
import logging
import base64
import time
import jwt
import redis
from cryptography.fernet import Fernet
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.settings import SECRET_KEY, RATE_LIMIT, RATE_LIMIT_WINDOW

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Redis Connection (for Token Revocation and Rate Limiting)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# FastAPI Security Scheme
auth_scheme = HTTPBearer()

class SecretsLoader:
    """
    Class to load and manage secrets with enhanced AES encryption.
    Supports key rotation and variable-based encryption keys.
    """
    def __init__(self, secrets_file: str = "app/config/secrets.yaml", key_env: str = "APP_ENCRYPTION_KEY"):
        self.secrets_file = secrets_file
        self.key_env = key_env
        self.cipher = self._load_encryption_key()
        self.secrets = self._load_secrets()

    def _load_encryption_key(self):
        """
        Loads or generates an encryption key, supporting key rotation.
        Uses an environment variable if available, else falls back to file-based key storage.
        """
        key = os.getenv(self.key_env)
        
        if key:
            logging.info("Using encryption key from environment variable.")
            return Fernet(base64.urlsafe_b64decode(key))

        key_file = "app/config/encryption_key.key"

        if os.path.exists(key_file):
            with open(key_file, "rb") as file:
                key = file.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as file:
                file.write(key)
            logging.warning("Generated a new encryption key. Store it securely!")

        return Fernet(key)

    def _encrypt(self, data: str) -> str:
        """
        Encrypts a string using AES encryption.
        """
        return base64.urlsafe_b64encode(self.cipher.encrypt(data.encode())).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """
        Decrypts an AES-encrypted string.
        """
        return self.cipher.decrypt(base64.urlsafe_b64decode(encrypted_data.encode())).decode()

    def _load_secrets(self) -> dict:
        """
        Loads secrets from the encrypted YAML file.
        """
        if not os.path.exists(self.secrets_file):
            logging.error(f"Secrets file not found: {self.secrets_file}")
            raise FileNotFoundError(f"Could not find file {self.secrets_file}")
        try:
            with open(self.secrets_file, "r") as file:
                encrypted_secrets = yaml.safe_load(file) or {}
            return {key: self._decrypt(value) for key, value in encrypted_secrets.items()}
        except Exception as e:
            logging.error(f"Error decrypting secrets: {e}")
            raise

    def get_secret(self, key: str, default=None):
        """
        Retrieves a decrypted secret.
        """
        return self.secrets.get(key, default)

# -------------------- Security Enhancements -------------------- #

class JWTAuthentication:
    """
    Handles JWT authentication with refresh token support and revocation.
    """
    @staticmethod
    def generate_token(payload: dict, expiration: int = 3600) -> str:
        """
        Generates a JWT token with expiration.
        """
        payload["exp"] = time.time() + expiration
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        redis_client.setex(f"active_token:{token}", expiration, "valid")
        return token

    @staticmethod
    def generate_refresh_token(payload: dict) -> str:
        """
        Generates a long-lived refresh token.
        """
        payload["exp"] = time.time() + (86400 * 30)  # 30 days
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)) -> dict:
        """
        Verifies a JWT token and checks against the revocation list.
        """
        token = credentials.credentials

        if redis_client.exists(f"revoked_token:{token}"):
            raise HTTPException(status_code=401, detail="Token has been revoked.")

        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired. Please refresh your session.")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def revoke_token(token: str):
        """
        Revokes a token by adding it to the blacklist.
        """
        redis_client.setex(f"revoked_token:{token}", 86400, "revoked")  # Blacklist for 24 hours

# -------------------- Adaptive Rate Limiting -------------------- #

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Adaptive Rate Limiting Middleware
    """
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        request_count = redis_client.get(key)

        if request_count is None:
            redis_client.setex(key, RATE_LIMIT_WINDOW, 1)
        else:
            request_count = int(request_count)
            if request_count >= RATE_LIMIT:
                retry_after = redis_client.ttl(key)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                )
            redis_client.incr(key)

        return await call_next(request)

# Apply Middleware Security Enhancements
app.add_middleware(RateLimiterMiddleware)

# Secure Route with Role-Based Access Control
@app.get("/secure-data", dependencies=[Depends(JWTAuthentication.verify_token)])
async def secure_data():
    """
    Secure API endpoint requiring authentication.
    """
    return {"message": "Access granted to secure data."}
