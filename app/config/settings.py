import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env
load_dotenv()

class Config(BaseSettings):
    # === GENERAL SYSTEM CONFIGURATION ===
    APP_NAME: str = "BruceAI"
    VERSION: str = "3.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # === FRONTEND URL ===
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # === REDIS / CACHING ===
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # === DATABASE ===
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bruce.db")

    # === AI MODEL PATHS (ALINEADOS CON .env) ===
    TINYLLAMA_MODEL_PATH: str = os.getenv("TINYLLAMA_MODEL_PATH", "./models/Tinyllama")
    PHI3_MODEL_PATH: str = os.getenv("PHI3_MODEL_PATH", "./models/Phi-3-mini-4k-instruct")
    DEEPSEEK_MODEL_PATH: str = os.getenv("DEEPSEEK_MODEL_PATH", "./models/deepseek")

    # === CRYPTO TRADING CONFIG ===
    TRADING_PAIR: str = os.getenv("TRADING_PAIR", "BTC-USDT")
    EXCHANGE: str = os.getenv("EXCHANGE", "OKX")
    OKX_WEBSOCKET_URI: str = os.getenv("OKX_WEBSOCKET_URI", "wss://ws.okx.com:8443/ws/v5/public")

    # ✅ Dummy values to prevent crashes during development
    OKX_API_KEY: str = os.getenv("OKX_API_KEY", "dummy_key")
    OKX_SECRET_KEY: str = os.getenv("OKX_API_SECRET", "dummy_secret")
    OKX_PASSPHRASE: str = os.getenv("OKX_PASSPHRASE", "dummy_passphrase")
    OKX_USE_SERVER_TIME: bool = os.getenv("OKX_USE_SERVER_TIME", "false").lower() == "true"

    # === VECTOR STORAGE & LOGGING ===
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_memory.json")
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO")

    # === AUDIO CONFIG ===
    AUDIO_MODE: str = os.getenv("AUDIO_MODE", "simulate")  # simulate, local, federico, external

    # === TERMINAL CONFIG ===
    TERMINAL_DEFAULT_MODEL: str = os.getenv("PRIMARY_MODEL", "phi3")  # se alinea con .env

    # === SELF-REFLECTION CONFIG ===
    SELF_REFLECTION_ENABLED: bool = os.getenv("ENABLE_SELF_REFLECTION", "true").lower() == "true"

    # === SECURITY ===
    API_KEY: str = os.getenv("API_KEY", "dev-api-key")
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")  # 🔐 Evita crash en endpoints

    # === ALERT / NOTIFICATION SYSTEM ===
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # === Pydantic Settings V2 Metadata ===
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Global configuration instance
config = Config()
