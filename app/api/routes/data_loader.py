from fastapi import APIRouter, File, UploadFile, Query, Form
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import os
import pandas as pd
import shutil
import tempfile
from typing import Optional
import ccxt

router = APIRouter(prefix="/market", tags=["Market Data"])

DATA_DIR = "data/processed"
PREVIEW_ROWS = 50

@router.post("/upload")
async def upload_market_data(
    file: UploadFile = File(...),
    market: str = Form(...),
    timeframe: str = Form("1m"),
    source: str = Form("file")
):
    os.makedirs(DATA_DIR, exist_ok=True)
    temp_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataframe(temp_path)
        if df is None:
            raise HTTPException(status_code=400, detail="Unsupported or invalid file format.")

        return {
            "status": "success",
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(PREVIEW_ROWS).to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.get("/fetch")
async def fetch_market_data(
    symbol: str = Query(..., description="Market symbol like BTC/USDT"),
    exchange: str = Query("binance"),
    timeframe: str = Query("1m"),
    limit: int = Query(500)
):
    try:
        exchange = exchange.lower()
        if exchange == "binance":
            ex = ccxt.binance()
        elif exchange == "kucoin":
            ex = ccxt.kucoin()
        else:
            raise HTTPException(status_code=400, detail="Exchange not supported yet.")

        data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        return {
            "status": "success",
            "rows": len(df),
            "preview": df.head(PREVIEW_ROWS).to_dict(orient="records"),
            "columns": list(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from exchange: {str(e)}")

@router.get("/info/supported")
def get_supported_sources():
    return {
        "exchanges": ["binance", "kucoin"],
        "file_formats": [".csv", ".json", ".parquet"],
        "timeframes": ["1m", "5m", "15m", "1h", "1d"]
    }

def load_dataframe(path: str) -> Optional[pd.DataFrame]:
    ext = os.path.splitext(path)[-1]
    try:
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext == ".json":
            return pd.read_json(path)
        elif ext == ".parquet":
            return pd.read_parquet(path)
    except Exception:
        return None
    return None
