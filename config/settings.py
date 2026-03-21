"""
Bruce AI - Configuración centralizada con validación.
Usa Pydantic BaseSettings para cargar y validar variables de entorno.
"""

import os
import secrets
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "info"
    secret_key: str = secrets.token_hex(32)
    allowed_hosts: str = "localhost,127.0.0.1"
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # --- Vector DB ---
    vector_db_path: str = "./vector_db/faiss.index"

    # --- JWT ---
    jwt_secret_key: str = secrets.token_hex(32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # --- AI Models ---
    primary_model: str = "phi3"
    fallback_models: str = "deepseek,tinyllama"
    model_mode: str = "auto"
    phi3_model_path: str = "./models/Phi-3-mini-4k-instruct"
    deepseek_model_path: str = "./models/deepseek-coder-1.3b-base"
    tinyllama_model_path: str = "./models/Tinyllama"
    deepseek_api_url: str = "http://localhost:8000/deepseek-api"
    deepseek_api_key: str = ""

    # --- Speech & Avatar ---
    enable_speech: bool = True
    voice_id: str = "bruce-founder"
    language_default: str = "en"
    multilanguage_support: bool = True
    enable_video_reports: bool = True
    avatar_style: str = "realistic"

    # --- Trading ---
    enable_trading: bool = True
    trading_mode: str = "auto"
    supported_exchanges: str = "binance,coinbase,kraken,okx"
    sniping_engine: str = "sniper_solana_ultra"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    enable_sniping: bool = False
    slippage_tolerance: float = 0.5
    mev_protection_enabled: bool = True

    # --- Arbitrage ---
    enable_arbitrage: bool = True
    arbitrage_modes: str = "triangular,sintetico,temporal,espacial"
    darkpool_access_enabled: bool = False
    darkpool_nodes: str = ""

    # --- External API Keys ---
    market_data_api_key: str = ""
    crypto_exchange_key: str = ""
    ai_sentiment_key: str = ""
    freight_api_key: str = ""

    # --- Storage ---
    temp_file_dir: str = "/tmp/bruce-models"
    upload_dir: str = "./uploads"
    max_memory_usage: str = "8GB"

    # --- Logging ---
    logging_level: str = "info"
    log_file_path: str = "./logs/bruce.log"
    log_rotation_size: str = "10MB"
    log_retention_days: int = 30
    monitoring_enabled: bool = True
    prometheus_exporter: bool = True

    # --- Admin & Security ---
    admin_password: str = secrets.token_hex(16)
    allowed_admin_ips: str = "127.0.0.1"
    encryption_key: str = secrets.token_hex(32)
    salt_secret: str = secrets.token_hex(16)

    # --- WebSocket ---
    ws_host: str = "localhost"
    ws_port: int = 3001

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./bruce.db"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # --- Exchange Keys ---
    okx_api_key: str = ""
    okx_api_secret: str = ""
    okx_passphrase: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @property
    def fallback_models_list(self) -> List[str]:
        return [m.strip() for m in self.fallback_models.split(",")]

    @property
    def supported_exchanges_list(self) -> List[str]:
        return [e.strip() for e in self.supported_exchanges.split(",")]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8-sig",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
