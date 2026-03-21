"""
DeepSeek Editor for Bruce Wayne v1
Este módulo permite que Bruce analice y modifique su propio código fuente usando AST y memoria simbólica.
Incluye protecciones de seguridad, modo de simulación y rollback.
"""

import ast
import os
import shutil
import difflib
from typing import Optional

class DeepSeekEditor:
    def __init__(self, source_dir: str, snapshot_dir: str, enable_simulation: bool = True):
        self.source_dir = source_dir
        self.snapshot_dir = snapshot_dir
        self.enable_simulation = enable_simulation
        os.makedirs(snapshot_dir, exist_ok=True)

    def create_snapshot(self):
        snapshot_path = os.path.join(self.snapshot_dir, "snapshot")
        if os.path.exists(snapshot_path):
            shutil.rmtree(snapshot_path)
        shutil.copytree(self.source_dir, snapshot_path)
        return snapshot_path

    def rollback_snapshot(self):
        snapshot_path = os.path.join(self.snapshot_dir, "snapshot")
        if os.path.exists(snapshot_path):
            shutil.rmtree(self.source_dir)
            shutil.copytree(snapshot_path, self.source_dir)
            return True
        return False

    def analyze_and_edit(self, target_file: str, transformation_fn: callable, dry_run: bool = True) -> Optional[str]:
        full_path = os.path.join(self.source_dir, target_file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Target file {target_file} not found.")

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return f"Syntax error in file {target_file}: {e}"

        modified_tree = transformation_fn(tree)
        new_source = ast.unparse(modified_tree)

        if dry_run or self.enable_simulation:
            diff = difflib.unified_diff(
                source.splitlines(),
                new_source.splitlines(),
                fromfile="original",
                tofile="modified",
                lineterm=""
            )
            return "\n".join(diff)
        else:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_source)
            return None

    def list_editable_files(self):
        return [f for f in os.listdir(self.source_dir) if f.endswith(".py") and not f.startswith("_")]

    def superuser_permission_granted(self):
        return os.environ.get("BRUCE_SUPERUSER_MODE", "false").lower() == "true"


# Ejemplo de transformación: insertar un print al inicio de cada función
def example_transformation(tree: ast.AST) -> ast.AST:
    class Transformer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            print_node = ast.parse("print('Entrando en función:', '{}')".format(node.name)).body[0]
            node.body.insert(0, print_node)
            return node
    return Transformer().visit(tree)
