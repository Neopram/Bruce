"""
strategic_controller.py – Bruce's Core Symbiotic Evolution Engine
Permite autoevaluación, automejora, generación de metaagentes, y control total del backend.
"""

import os
import json
import shutil
from datetime import datetime
from introspector import BruceIntrospector

class BruceStrategicController:
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.meta_path = os.path.join(base_path, "meta_reports")
        os.makedirs(self.meta_path, exist_ok=True)

    def system_diagnostics(self):
        inspector = BruceIntrospector(base_path=self.base_path)
        report = inspector.generate_report()
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        report_path = os.path.join(self.meta_path, f"diagnostic_{timestamp}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return report

    def generate_meta_agent(self, name: str, purpose: str, behaviors: list):
        """Crea un archivo de Python con estructura de agente personalizado"""
        safe_name = name.lower().replace(" ", "_")
        class_name = "".join(word.capitalize() for word in name.split())
        behaviors_formatted = json.dumps(behaviors, indent=4)

        agent_lines = [
            f'"""',
            f'MetaAgente: {name}',
            f'Propósito: {purpose}',
            f'Generado automáticamente por BruceStrategicController',
            f'"""',
            '',
            f'class {class_name}Agent:',
            f'    def __init__(self):',
            f'        self.name = "{name}"',
            f'        self.purpose = "{purpose}"',
            f'        self.behaviors = {behaviors_formatted}',
            '',
            f'    def run(self):',
            f'        print(f"[META-AGENTE ACTIVADO] {{self.name}} ejecutando comportamiento principal...")',
            f'        for behavior in self.behaviors:',
            f'            print(f"→ Ejecutando: {{behavior}}")'
        ]

        agent_code = "\n".join(agent_lines)
        agent_file = os.path.join(self.base_path, f"{safe_name}_agent.py")
        with open(agent_file, "w", encoding="utf-8") as f:
            f.write(agent_code)

        return {"status": "created", "agent": agent_file}

    def self_modify_code(self, target_file: str, old_str: str, new_str: str):
        """Sustituye código en un archivo dado de forma segura"""
        full_path = os.path.join(self.base_path, target_file)
        if not os.path.exists(full_path):
            return {"error": "File not found"}

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_str not in content:
            return {"error": "String to replace not found"}

        backup_path = full_path + ".bak"
        shutil.copy(full_path, backup_path)

        updated_content = content.replace(old_str, new_str)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return {"status": "modified", "backup": backup_path, "modified_file": full_path}

if __name__ == "__main__":
    controller = BruceStrategicController(base_path=".")
    diag = controller.system_diagnostics()
    print("=== DIAGNÓSTICO COMPLETO ===")
    print(json.dumps(diag, indent=2))
    agent = controller.generate_meta_agent(
        name="Quantum Analyst",
        purpose="Explorar relaciones cuánticas en los mercados",
        behaviors=["análisis de correlaciones", "detectar patrones no lineales"]
    )
    print("Metaagente creado:", agent)
