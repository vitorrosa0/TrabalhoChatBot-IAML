from typing import List, Optional
from . import IntentHandlers

class IntentClassifier:
    def __init__(self):
        self.handlers = [
            IntentHandlers.SynopsisHandler(),
            IntentHandlers.DirectorHandler(),
            IntentHandlers.ActorHandler(),
            IntentHandlers.TriviaHandler(),
            IntentHandlers.ContextualHandler()
        ]

    def classify(self, tokens: List[str]) -> str:
        for handler in self.handlers:
            if handler.matches(tokens):
                return handler.get_intent_name()
        return "unknown"