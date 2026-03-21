import redis
import json

class MemoryManager:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, db=0)

    def log_interaction(self, prompt, user):
        key = f"memory:{user}"
        self.redis.rpush(key, json.dumps({"prompt": prompt}))
        self.redis.ltrim(key, -3, -1)

    def store_decision(self, prompt, action_obj, user):
        key = f"memory:{user}"
        self.redis.rpush(key, json.dumps({"decision": action_obj}))
        self.redis.ltrim(key, -3, -1)

    def recall(self, user):
        key = f"memory:{user}"
        logs = self.redis.lrange(key, -3, -1)
        return [json.loads(entry) for entry in logs] if logs else []

    def summarize(self):
        return "[Resumen de decisiones almacenadas y reflexiones pasadas.]"
