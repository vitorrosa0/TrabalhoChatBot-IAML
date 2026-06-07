from typing import List
from nltk.stem import RSLPStemmer
from . import IntentHandlers
from .GreetingMLHandler import GreetingMLHandler
from .AffirmationHandler import AffirmationHandler

class IntentClassifier:
    def __init__(self, stemmer: RSLPStemmer):
        self.handlers = [
            GreetingMLHandler(stemmer), 
            AffirmationHandler(stemmer),
            IntentHandlers.GenreSearchHandler(stemmer),
            IntentHandlers.TriviaHandler(stemmer),
            IntentHandlers.SynopsisHandler(stemmer),
            IntentHandlers.DirectorHandler(stemmer),  
            IntentHandlers.ActorFilmographyHandler(stemmer),
            IntentHandlers.ActorHandler(stemmer),
            IntentHandlers.YearHandler(stemmer),
            IntentHandlers.GenreHandler(stemmer),
            IntentHandlers.AwardsHandler(stemmer),
            IntentHandlers.CastHandler(stemmer), 
            IntentHandlers.SimilarMoviesHandler(stemmer),
            IntentHandlers.ContextualHandler(stemmer),
        ]

    def get_affirmation_handler(self) -> "AffirmationHandler":
        for h in self.handlers:
            if isinstance(h, AffirmationHandler):
                return h

    def classify(self, tokens: List[str]) -> str:
        for handler in self.handlers:
            if handler.matches(tokens):
                # print(f"[DEBUG] match em: {handler.__class__.__name__}")
                return handler.get_intent_name()
        return "unknown"

    def get_keywords_for_intent(self, intent_name: str) -> List[str]:
        for handler in self.handlers:
            if handler.get_intent_name() == intent_name:
                return handler.get_stemmed_keywords()
        return []