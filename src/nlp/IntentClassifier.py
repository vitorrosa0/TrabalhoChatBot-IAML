from typing import List
from nltk.stem import RSLPStemmer
from . import IntentHandlers

class IntentClassifier:
    def __init__(self, stemmer: RSLPStemmer):
        self.handlers = [
            IntentHandlers.SynopsisHandler(stemmer),
            IntentHandlers.DirectorHandler(stemmer),  
            IntentHandlers.ActorHandler(stemmer),
            IntentHandlers.TriviaHandler(stemmer),
            IntentHandlers.YearHandler(stemmer),
            IntentHandlers.GenreHandler(stemmer),
            IntentHandlers.ContextualHandler(stemmer),
        ]

    def classify(self, tokens: List[str]) -> str:
        for handler in self.handlers:
            if handler.matches(tokens):
                return handler.get_intent_name()
        return "unknown"