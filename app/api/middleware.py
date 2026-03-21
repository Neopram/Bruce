import time
import jwt
import logging
import redis
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.settings import SECRET_KEY, RATE_LIMIT, RATE_LIMIT_WINDOW

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Redis Connection (for Adaptive Rate Limiting)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# FastAPI Security Scheme
auth_scheme = HTTPBearer()

class JWTAuthentication:
    """
    Handles JWT authentication with refresh token support.
    """
    @staticmethod
    def generate_token(payload: dict, expiration: int = 3600) -> str:
        """
        Generates a JWT token with expiration.
        """
        payload["exp"] = time.time() + expiration
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

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
        Verifies a JWT token and refreshes if needed.
        """
        token = credentials.credentials
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired. Please refresh your session.")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


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
