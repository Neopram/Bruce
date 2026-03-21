import time
import logging
import psutil
from deeptradex.tia_agent import TIAAgent

def run_observer_loop():
    agent = TIAAgent()
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        if cpu > 85 or mem > 85:
            logging.warning("🚨 High resource usage detected, invoking TIAAgent")
            context = {"cpu": cpu, "memory": mem}
            result = agent.execute("Predict system stability and recommend actions", context)
            logging.info(f"TIAAgent Response: {result}")
        time.sleep(60)