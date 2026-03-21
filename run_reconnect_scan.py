
from ai_core.reconnect_engine import DormantFunctionReconnector
import json

scanner = DormantFunctionReconnector(base_path="/mnt/data/_bruce_backend_total/bruce_backend")
dormant_funcs = scanner.scan_functions()

with open("reconnected_report.json", "w", encoding="utf-8") as f:
    json.dump(dormant_funcs, f, indent=4)
print(f"✅ Reconectadas: {len(dormant_funcs)} funciones detectadas.")
