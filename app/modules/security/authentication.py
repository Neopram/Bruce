import jwt
import datetime
import logging
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Security Constants
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Password Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthManager:
    """
    Manages authentication, JWT generation, and user validation.
    """
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verifies if a password matches its hashed version."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password):
        """Hashes a plaintext password."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
        """Generates a JWT access token."""
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str):
        """Decodes and validates a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def authenticate_user(username: str, password: str, user_db: dict):
        """Authenticates a user against a mock database."""
        if username in user_db and AuthManager.verify_password(password, user_db[username]):
            return True
        return False

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extracts the current user from JWT token."""
    return AuthManager.decode_access_token(token)

# Example Usage
if __name__ == "__main__":
    test_user = "admin"
    test_password = "secure_password"
    hashed_pw = AuthManager.hash_password(test_password)
    print(f"🔐 Hashed Password: {hashed_pw}")
    
    token = AuthManager.create_access_token({"sub": test_user})
    print(f"🔑 Generated Token: {token}")
    
    decoded = AuthManager.decode_access_token(token)
    print(f"✅ Decoded Token Data: {decoded}")
