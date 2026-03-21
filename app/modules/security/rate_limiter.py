import time
import logging
import redis
from fastapi import Request, HTTPException
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Redis Configuration
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0, decode_responses=True)

# Rate Limit Constants
RATE_LIMIT_WINDOW = 60  # Time window in seconds
RATE_LIMIT_MAX_REQUESTS = 100  # Maximum requests per user in time window

class RateLimiter:
    """
    Implements rate limiting using Redis to prevent API abuse.
    """
    @staticmethod
    def check_rate_limit(request: Request):
        """Applies rate limiting based on IP address."""
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        requests_made = redis_client.get(key)

        if requests_made and int(requests_made) >= RATE_LIMIT_MAX_REQUESTS:
            logging.warning(f"🚨 Rate limit exceeded for {client_ip}")
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        
        redis_client.incr(key)
        redis_client.expire(key, RATE_LIMIT_WINDOW)

        logging.info(f"✅ Request allowed: {client_ip} ({requests_made}/{RATE_LIMIT_MAX_REQUESTS})")
        return True

# Example Usage in FastAPI Middleware
from fastapi import FastAPI, Depends

app = FastAPI()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to enforce API rate limiting."""
    RateLimiter.check_rate_limit(request)
    response = await call_next(request)
    return response

@app.get("/protected-endpoint")
def protected_api():
    return {"message": "You have access to this resource!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
