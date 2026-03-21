
# memory.py
class MemoryManager:
    def __init__(self):
        self.logs = {}

    def log_interaction(self, prompt, user):
        self.logs.setdefault(user, []).append({ "prompt": prompt })

    def store_decision(self, prompt, action_obj, user):
        self.logs[user].append({ "decision": action_obj })

    def recall(self, user):
        return self.logs.get(user, [])[-3:] if user in self.logs else []

    def summarize(self):
        return "[Resumen de decisiones almacenadas y reflexiones pasadas.]"
