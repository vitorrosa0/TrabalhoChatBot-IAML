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
            IntentHandlers.AwardsHandler(stemmer),
            IntentHandlers.CastHandler(stemmer), 
            IntentHandlers.SimilarMoviesHandler(stemmer),
            IntentHandlers.ContextualHandler(stemmer),
        ]

    def classify(self, tokens: List[str]) -> str:
     for handler in self.handlers:
        if handler.matches(tokens):
            # print(f"[DEBUG] match em: {handler.__class__.__name__}")
            return handler.get_intent_name()
     return "unknown"