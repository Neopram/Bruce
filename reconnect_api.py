
from fastapi import APIRouter
import json
import os

router = APIRouter()

@router.get("/reconnect/functions")
async def list_reconnected_functions():
    report_path = "reconnected_report.json"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"functions": data}
    return {"functions": []}
