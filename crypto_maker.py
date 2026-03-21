# crypto_maker.py

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import logging

from personality import TraderProfile
# from volatility_guard import guardian_check  # Temporalmente desactivado
from user_biometrics import UserBiometrics
from vector_logger import VectorLogger

# Try Web3 for on-chain operations
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    Web3 = None
    WEB3_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger("Bruce.TokenMaker")

# Logger avanzado de tokens creados
token_logger = VectorLogger()
persona = TraderProfile()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TokenSpec(BaseModel):
    name: str
    symbol: str
    decimals: int = 9
    initial_supply: float
    blockchain: str  # "solana", "ethereum", "bsc"
    burnable: bool = True
    mint_authority: str
    metadata: dict = {}


class TokenMetadata(BaseModel):
    token_id: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    website: Optional[str] = None
    social_links: Dict[str, str] = {}
    tags: List[str] = []


class GasEstimateRequest(BaseModel):
    blockchain: str
    operation: str = "token_creation"
    priority: str = "medium"  # low, medium, high


class ContractVerificationRequest(BaseModel):
    token_id: str
    contract_address: str
    blockchain: str
    source_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Gas Estimator
# ---------------------------------------------------------------------------

class GasEstimator:
    """Estimates gas costs for on-chain operations. Uses Web3 when available."""

    # Rough gas units for common operations per chain
    _GAS_UNITS: Dict[str, Dict[str, int]] = {
        "ethereum": {"token_creation": 1_500_000, "transfer": 65_000, "approve": 46_000},
        "bsc": {"token_creation": 1_200_000, "transfer": 55_000, "approve": 46_000},
        "solana": {"token_creation": 5000, "transfer": 5000, "approve": 5000},
    }

    # Simulated gas prices in native currency units (Gwei for EVM, lamports for Solana)
    _GAS_PRICES: Dict[str, Dict[str, float]] = {
        "ethereum": {"low": 15.0, "medium": 25.0, "high": 50.0},
        "bsc": {"low": 3.0, "medium": 5.0, "high": 8.0},
        "solana": {"low": 0.000005, "medium": 0.000010, "high": 0.000025},
    }

    _NATIVE_PRICES_USD: Dict[str, float] = {
        "ethereum": 3450.0,
        "bsc": 610.0,
        "solana": 172.0,
    }

    def __init__(self, web3_instance=None):
        self._w3 = web3_instance

    def estimate(self, blockchain: str, operation: str = "token_creation",
                 priority: str = "medium") -> Dict[str, Any]:
        chain = blockchain.lower()
        gas_units = self._GAS_UNITS.get(chain, {}).get(operation, 1_000_000)
        gas_price_gwei = self._GAS_PRICES.get(chain, {}).get(priority, 25.0)
        native_price_usd = self._NATIVE_PRICES_USD.get(chain, 100.0)

        # If we have a live Web3 connection to an EVM chain, try getting real gas price
        live_gas = False
        if self._w3 and chain in ("ethereum", "bsc"):
            try:
                gp = self._w3.eth.gas_price
                gas_price_gwei = gp / 1e9
                live_gas = True
            except Exception:
                pass

        if chain == "solana":
            # Solana fees are flat per signature, not gas-based
            cost_native = gas_price_gwei  # already in SOL
        else:
            cost_native = gas_units * gas_price_gwei / 1e9

        cost_usd = cost_native * native_price_usd

        return {
            "blockchain": chain,
            "operation": operation,
            "priority": priority,
            "gas_units": gas_units,
            "gas_price_gwei": round(gas_price_gwei, 4),
            "cost_native": round(cost_native, 8),
            "cost_usd": round(cost_usd, 4),
            "native_token_price_usd": native_price_usd,
            "live_gas_price": live_gas,
            "estimated_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Contract Verification Manager (placeholder)
# ---------------------------------------------------------------------------

class ContractVerifier:
    """Placeholder for block-explorer contract verification (Etherscan, BSCScan, etc.)."""

    _EXPLORER_URLS: Dict[str, str] = {
        "ethereum": "https://etherscan.io",
        "bsc": "https://bscscan.com",
        "solana": "https://solscan.io",
    }

    def __init__(self):
        self.verification_queue: List[Dict[str, Any]] = []

    def submit_verification(self, token_id: str, contract_address: str,
                            blockchain: str, source_code: Optional[str] = None
                            ) -> Dict[str, Any]:
        record = {
            "verification_id": str(uuid.uuid4()),
            "token_id": token_id,
            "contract_address": contract_address,
            "blockchain": blockchain.lower(),
            "status": "queued",
            "explorer_url": self._EXPLORER_URLS.get(blockchain.lower(), "unknown"),
            "submitted_at": datetime.utcnow().isoformat(),
            "message": "Verification queued. In production this would call the block explorer API.",
        }
        self.verification_queue.append(record)
        logger.info(f"Contract verification submitted: {record['verification_id']}")
        return record

    def get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        for v in self.verification_queue:
            if v["verification_id"] == verification_id:
                return v
        return {"error": f"Verification {verification_id} not found"}


# ---------------------------------------------------------------------------
# Token Metadata Manager
# ---------------------------------------------------------------------------

class TokenMetadataManager:
    """Manages off-chain token metadata (name, image, links, etc.)."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def set_metadata(self, token_id: str, description: Optional[str] = None,
                     image_url: Optional[str] = None, website: Optional[str] = None,
                     social_links: Optional[Dict[str, str]] = None,
                     tags: Optional[List[str]] = None) -> Dict[str, Any]:
        existing = self._store.get(token_id, {})
        if description is not None:
            existing["description"] = description
        if image_url is not None:
            existing["image_url"] = image_url
        if website is not None:
            existing["website"] = website
        if social_links is not None:
            existing["social_links"] = social_links
        if tags is not None:
            existing["tags"] = tags
        existing["updated_at"] = datetime.utcnow().isoformat()
        self._store[token_id] = existing
        return {"token_id": token_id, "metadata": existing}

    def get_metadata(self, token_id: str) -> Dict[str, Any]:
        meta = self._store.get(token_id)
        if not meta:
            return {"token_id": token_id, "metadata": None}
        return {"token_id": token_id, "metadata": meta}


# ---------------------------------------------------------------------------
# Web3 Connection Helper
# ---------------------------------------------------------------------------

class Web3Manager:
    """Manages Web3 connections for EVM-compatible chains."""

    _DEFAULT_RPCS: Dict[str, str] = {
        "ethereum": "https://eth.llamarpc.com",
        "bsc": "https://bsc-dataseed.binance.org",
    }

    def __init__(self):
        self._connections: Dict[str, Any] = {}

    def get_connection(self, blockchain: str, rpc_url: Optional[str] = None):
        chain = blockchain.lower()
        if chain in self._connections:
            return self._connections[chain]

        if not WEB3_AVAILABLE:
            logger.info(f"Web3 not installed, cannot connect to {chain}")
            return None

        url = rpc_url or self._DEFAULT_RPCS.get(chain)
        if not url:
            return None

        try:
            w3 = Web3(Web3.HTTPProvider(url))
            if w3.is_connected():
                self._connections[chain] = w3
                logger.info(f"Web3 connected to {chain} via {url}")
                return w3
        except Exception as exc:
            logger.warning(f"Web3 connection failed for {chain}: {exc}")

        return None

    def get_chain_info(self, blockchain: str) -> Dict[str, Any]:
        w3 = self.get_connection(blockchain)
        if w3:
            try:
                return {
                    "blockchain": blockchain,
                    "connected": True,
                    "chain_id": w3.eth.chain_id,
                    "block_number": w3.eth.block_number,
                    "gas_price_gwei": round(w3.eth.gas_price / 1e9, 4),
                }
            except Exception as exc:
                return {"blockchain": blockchain, "connected": False, "error": str(exc)}

        return {
            "blockchain": blockchain,
            "connected": False,
            "web3_available": WEB3_AVAILABLE,
            "message": "Simulated mode - no live RPC connection",
        }


# ---------------------------------------------------------------------------
# Token Creator (expanded)
# ---------------------------------------------------------------------------

class TokenCreator:
    def __init__(self):
        self.history = []
        self.gas_estimator = GasEstimator()
        self.contract_verifier = ContractVerifier()
        self.metadata_manager = TokenMetadataManager()
        self.web3_manager = Web3Manager()

    def create_token(self, spec: TokenSpec):
        # Validaciones clave
        if not spec.name or not spec.symbol:
            raise ValueError("El nombre y simbolo son obligatorios.")
        if spec.initial_supply <= 0:
            raise ValueError("El suministro inicial debe ser mayor a cero.")
        if spec.blockchain.lower() not in ["solana", "ethereum", "bsc"]:
            raise ValueError("Blockchain no soportada.")

        # Gas estimation
        gas_estimate = self.gas_estimator.estimate(spec.blockchain, "token_creation", "medium")

        # Check Web3 connectivity
        chain_info = self.web3_manager.get_chain_info(spec.blockchain)

        # Simulacion de creacion
        token_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        log = {
            "token_id": token_id,
            "name": spec.name,
            "symbol": spec.symbol,
            "decimals": spec.decimals,
            "initial_supply": spec.initial_supply,
            "blockchain": spec.blockchain,
            "burnable": spec.burnable,
            "mint_authority": spec.mint_authority,
            "persona": persona.current_profile(),
            "created_at": timestamp,
            "metadata": spec.metadata,
            "gas_estimate": gas_estimate,
            "chain_info": chain_info,
        }

        self.history.append(log)
        token_logger.log_event("TOKEN_CREATED", log)
        logger.info(f"[BRUCE] Token creado: {log}")

        # Auto-set basic metadata
        if spec.metadata:
            self.metadata_manager.set_metadata(
                token_id,
                description=spec.metadata.get("description"),
                image_url=spec.metadata.get("image_url"),
                website=spec.metadata.get("website"),
                tags=spec.metadata.get("tags", []),
            )

        return {
            "status": "Token virtual creado exitosamente (modo simulado)",
            "token_id": token_id,
            "created_at": timestamp,
            "persona": persona.current_profile(),
            "guardian_status": None,
            "biometrics": UserBiometrics().read(),
            "gas_estimate": gas_estimate,
            "chain_info": chain_info,
            "token": log,
        }


# Instancia del generador
bruce_token_creator = TokenCreator()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/token-maker")
async def token_maker_endpoint(req: Request):
    try:
        data = await req.json()
        token_spec = TokenSpec(**data)
        result = bruce_token_creator.create_token(token_spec)
        return result
    except Exception as e:
        logger.error(f"[ERROR] Fallo al crear token: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/token-maker/history")
async def get_token_creation_history():
    return {
        "total_created": len(bruce_token_creator.history),
        "tokens": bruce_token_creator.history,
    }


@router.post("/token-maker/gas-estimate")
async def gas_estimate_endpoint(req: Request):
    data = await req.json()
    gas_req = GasEstimateRequest(**data)
    return bruce_token_creator.gas_estimator.estimate(
        gas_req.blockchain, gas_req.operation, gas_req.priority
    )


@router.post("/token-maker/verify-contract")
async def verify_contract_endpoint(req: Request):
    data = await req.json()
    ver_req = ContractVerificationRequest(**data)
    return bruce_token_creator.contract_verifier.submit_verification(
        ver_req.token_id, ver_req.contract_address, ver_req.blockchain, ver_req.source_code
    )


@router.get("/token-maker/verification/{verification_id}")
async def verification_status_endpoint(verification_id: str):
    return bruce_token_creator.contract_verifier.get_verification_status(verification_id)


@router.post("/token-maker/metadata")
async def set_metadata_endpoint(req: Request):
    data = await req.json()
    meta = TokenMetadata(**data)
    return bruce_token_creator.metadata_manager.set_metadata(
        meta.token_id,
        description=meta.description,
        image_url=meta.image_url,
        website=meta.website,
        social_links=meta.social_links,
        tags=meta.tags,
    )


@router.get("/token-maker/metadata/{token_id}")
async def get_metadata_endpoint(token_id: str):
    return bruce_token_creator.metadata_manager.get_metadata(token_id)


@router.get("/token-maker/chain-info/{blockchain}")
async def chain_info_endpoint(blockchain: str):
    return bruce_token_creator.web3_manager.get_chain_info(blockchain)


@router.get("/token-maker/status")
async def token_maker_status_endpoint():
    return {
        "web3_available": WEB3_AVAILABLE,
        "supported_blockchains": ["ethereum", "bsc", "solana"],
        "total_tokens_created": len(bruce_token_creator.history),
        "pending_verifications": len(bruce_token_creator.contract_verifier.verification_queue),
    }
