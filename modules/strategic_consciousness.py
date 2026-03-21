
import ast
import os
import difflib

try:
    from modules.memory import record_memory
except ImportError:
    def record_memory(msg):
        pass

try:
    from modules.vector_logger import vector_log
except ImportError:
    def vector_log(msg):
        pass

class StrategicConsciousness:
    def __init__(self, root_path="./"):
        self.root_path = root_path
        self.snapshots_dir = os.path.join(root_path, "snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def analyze_file(self, file_path):
        full_path = os.path.join(self.root_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            return functions
        except Exception as e:
            return f"Error analyzing {file_path}: {str(e)}"

    def propose_improvement(self, file_path, target_function, transformation):
        full_path = os.path.join(self.root_path, file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            original_code = f.readlines()

        modified_code = []
        inside_target = False

        for line in original_code:
            if target_function in line:
                inside_target = True
            if inside_target and line.strip().startswith("def "):
                modified_code.append(f"    # Strategic hook injected here\n")
            modified_code.append(line)

        snapshot_path = os.path.join(self.snapshots_dir, f"{os.path.basename(file_path)}.bak")
        with open(snapshot_path, "w", encoding="utf-8") as backup:
            backup.writelines(original_code)

        with open(full_path, "w", encoding="utf-8") as modified:
            modified.writelines(modified_code)

        vector_log(f"Improved {target_function} in {file_path}")
        record_memory(f"Function {target_function} was modified with strategic transformation.")

        diff = difflib.unified_diff(original_code, modified_code, lineterm="")
        return "\n".join(diff)

# Ejemplo de uso interno:
# sc = StrategicConsciousness(root_path="./")
# print(sc.analyze_file("modules/self_reflection.py"))
# print(sc.propose_improvement("modules/self_reflection.py", "self_reflect", "hook"))
