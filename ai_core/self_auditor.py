
import os
import ast

class BruceSelfAuditor:
    def __init__(self, base_path=".", ignored_folders=None):
        self.base_path = base_path
        self.ignored_folders = ignored_folders or ["venv", "__pycache__", "node_modules"]
        self.results = {
            "total_files": 0,
            "total_functions": 0,
            "unconnected_functions": [],
        }

    def scan_python_files(self):
        py_files = []
        for root, _, files in os.walk(self.base_path):
            if any(folder in root for folder in self.ignored_folders):
                continue
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        return py_files

    def extract_functions(self, file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except Exception:
            return []

    def analyze(self):
        files = self.scan_python_files()
        self.results["total_files"] = len(files)
        all_functions = {}

        for file in files:
            funcs = self.extract_functions(file)
            self.results["total_functions"] += len(funcs)
            all_functions[file] = funcs

        disconnected = []
        for path, funcs in all_functions.items():
            for func in funcs:
                found = False
                for other_path, content in all_functions.items():
                    if other_path != path:
                        with open(other_path, "r", encoding="utf-8", errors="ignore") as f:
                            if any(func in line for line in f):
                                found = True
                                break
                if not found:
                    disconnected.append({"file": path, "function": func})
        self.results["unconnected_functions"] = disconnected
        return self.results
