from transformers import pipeline

class TraderProfile:
    def __init__(self):
        self.analyzer = pipeline("sentiment-analysis")
        self.persona = "neutro"

    def update(self, text):
        sentiment = self.analyzer(text)[0]
        if sentiment['label'] == 'POSITIVE':
            self.persona = "agresivo"
        elif sentiment['label'] == 'NEGATIVE':
            self.persona = "conservador"
        else:
            self.persona = "neutro"

    def current_profile(self):
        return self.persona
