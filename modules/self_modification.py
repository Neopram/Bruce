"""
Self-modifying code engine (sandboxed).
Analyzes own source code, suggests improvements, and applies safe
modifications with snapshot-based rollback support.
"""
import os
import shutil
import hashlib
import ast
from datetime import datetime
from fastapi import APIRouter, Query


router = APIRouter()

BASE_PATH = os.getenv("SOURCE_CODE_DIR", "./")
SNAPSHOT_PATH = os.getenv("SNAPSHOT_DIR", "./snapshots")
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"


class SelfModificationEngine:
    """Sandboxed engine for analyzing and modifying source code safely."""

    def __init__(self, source_dir=None, snapshot_dir=None, simulation=True):
        self.source_dir = source_dir or BASE_PATH
        self.snapshot_dir = snapshot_dir or SNAPSHOT_PATH
        self.simulation = simulation
        self.modification_log = []
        self.snapshots = []

    def analyze_file(self, filepath):
        """Analyze a Python file and return structural information."""
        full_path = os.path.join(self.source_dir, filepath)
        if not os.path.exists(full_path):
            return {"status": "error", "message": f"File not found: {filepath}"}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            classes = []
            functions = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes.append({"name": node.name, "methods": methods, "line": node.lineno})
                elif isinstance(node, ast.FunctionDef):
                    if not any(node.lineno > c["line"] for c in classes):
                        functions.append({"name": node.name, "line": node.lineno})
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.dump(node))

            return {
                "filepath": filepath,
                "lines": len(source.splitlines()),
                "classes": classes,
                "top_level_functions": functions,
                "import_count": len(imports),
                "file_hash": hashlib.md5(source.encode()).hexdigest(),
            }
        except SyntaxError as e:
            return {"status": "error", "message": f"Syntax error: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def suggest_improvements(self, filepath):
        """Analyze a file and suggest code improvements."""
        analysis = self.analyze_file(filepath)
        if analysis.get("status") == "error":
            return analysis

        suggestions = []
        for cls in analysis.get("classes", []):
            if len(cls["methods"]) > 15:
                suggestions.append({
                    "type": "refactor",
                    "target": cls["name"],
                    "message": f"Class '{cls['name']}' has {len(cls['methods'])} methods - consider splitting",
                })
            for method in cls["methods"]:
                if not method.startswith("_") and len(method) < 3:
                    suggestions.append({
                        "type": "naming",
                        "target": f"{cls['name']}.{method}",
                        "message": f"Method name '{method}' is very short - consider a descriptive name",
                    })

        if analysis.get("lines", 0) > 500:
            suggestions.append({
                "type": "size",
                "target": filepath,
                "message": f"File has {analysis['lines']} lines - consider splitting into modules",
            })

        return {"filepath": filepath, "suggestions": suggestions, "count": len(suggestions)}

    def create_snapshot(self, filepath=None):
        """Create a snapshot of current source for rollback."""
        os.makedirs(self.snapshot_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"snapshot_{timestamp}"
        snapshot_path = os.path.join(self.snapshot_dir, snapshot_name)

        if self.simulation:
            entry = {"name": snapshot_name, "path": snapshot_path, "simulated": True,
                     "created_at": datetime.utcnow().isoformat()}
            self.snapshots.append(entry)
            return entry

        try:
            if filepath:
                src = os.path.join(self.source_dir, filepath)
                os.makedirs(snapshot_path, exist_ok=True)
                dst = os.path.join(snapshot_path, os.path.basename(filepath))
                shutil.copy2(src, dst)
            else:
                shutil.copytree(self.source_dir, snapshot_path, dirs_exist_ok=True)

            entry = {"name": snapshot_name, "path": snapshot_path, "simulated": False,
                     "created_at": datetime.utcnow().isoformat()}
            self.snapshots.append(entry)
            return entry
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def apply_modification(self, filepath, old_text, new_text, dry_run=True):
        """Apply a text replacement modification to a file."""
        full_path = os.path.join(self.source_dir, filepath)
        if not os.path.exists(full_path):
            return {"status": "error", "message": f"File not found: {filepath}"}

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_text not in content:
            return {"status": "error", "message": "Target text not found in file"}

        new_content = content.replace(old_text, new_text, 1)

        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return {"status": "error", "message": f"Modification would create syntax error: {e}"}

        if dry_run or self.simulation:
            entry = {"filepath": filepath, "status": "dry_run", "valid_syntax": True,
                     "timestamp": datetime.utcnow().isoformat()}
            self.modification_log.append(entry)
            return entry

        self.create_snapshot(filepath)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        entry = {"filepath": filepath, "status": "applied",
                 "timestamp": datetime.utcnow().isoformat()}
        self.modification_log.append(entry)
        return entry

    def rollback(self, snapshot_name=None):
        """Rollback to a previous snapshot."""
        if not self.snapshots:
            return {"status": "error", "message": "No snapshots available"}

        target = None
        if snapshot_name:
            target = next((s for s in self.snapshots if s["name"] == snapshot_name), None)
        else:
            target = self.snapshots[-1]

        if not target:
            return {"status": "error", "message": "Snapshot not found"}

        if target.get("simulated"):
            return {"status": "simulated_rollback", "snapshot": target["name"]}

        try:
            if os.path.isdir(target["path"]):
                shutil.copytree(target["path"], self.source_dir, dirs_exist_ok=True)
            return {"status": "rolled_back", "snapshot": target["name"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_modification_log(self, limit=20):
        """Return recent modification log."""
        return self.modification_log[-limit:]

    def get_snapshots(self):
        """Return list of available snapshots."""
        return self.snapshots


_engine = SelfModificationEngine(source_dir=BASE_PATH, snapshot_dir=SNAPSHOT_PATH, simulation=SIMULATION_MODE)


@router.get("/api/self-rewrite")
def self_rewrite(
    file: str = Query(..., description="Target Python file to analyze and edit"),
    simulate: bool = Query(True, description="Whether to simulate the changes"),
):
    """Analyze a file and suggest modifications."""
    try:
        _engine.create_snapshot(file)
        analysis = _engine.analyze_file(file)
        suggestions = _engine.suggest_improvements(file)
        return {
            "status": "success",
            "file": file,
            "simulated": simulate,
            "analysis": analysis,
            "suggestions": suggestions,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
