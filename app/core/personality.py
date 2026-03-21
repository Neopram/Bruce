
# personality.py
class TraderProfile:
    def __init__(self):
        self.persona = "neutro"

    def update(self, text):
        if "arriesgado" in text.lower():
            self.persona = "agresivo"
        elif "cautela" in text.lower():
            self.persona = "conservador"

    def current_profile(self):
        return self.persona
