
import importlib.util
import os
import ast

class DormantFunctionReconnector:
    def __init__(self, base_path):
        self.base_path = base_path
        self.dormant_functions = []

    def scan_functions(self):
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=file)
                            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                            for func in functions:
                                self.dormant_functions.append({
                                    "file": os.path.relpath(path, self.base_path),
                                    "function": func
                                })
                    except Exception as e:
                        print(f"Error reading {path}: {e}")
        return self.dormant_functions

    def generate_router_blueprint(self, output_path="reconnected_routes.py"):
        grouped = {}
        for entry in self.dormant_functions:
            f = entry['file'].replace("\\", "/")
            if f not in grouped:
                grouped[f] = []
            grouped[f].append(entry["function"])

        with open(output_path, "w", encoding="utf-8") as out:
            out.write("from fastapi import APIRouter\n")
            out.write("router = APIRouter()\n\n")
            for module, funcs in grouped.items():
                module_path = module.replace("/", ".").replace(".py", "")
                out.write(f"try:\n\tfrom {module_path} import {', '.join(funcs)}\n")
                for func in funcs:
                    out.write(f"\t@router.get('/reconnect/{func}')\n")
                    out.write(f"\tasync def {func}_reconnect(): return {func}()\n")
                out.write("except Exception as e:\n\tprint(f'Error loading module {module_path}:', e)\n\n")
        return output_path
