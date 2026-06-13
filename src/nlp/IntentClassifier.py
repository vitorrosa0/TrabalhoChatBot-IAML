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
            IntentHandlers.PersonSearchHandler(stemmer),   # antes de genre/country para capturar "filmes do [Nome]"
            IntentHandlers.GenreSearchHandler(stemmer),
            IntentHandlers.CountrySearchHandler(stemmer),
            IntentHandlers.TriviaHandler(stemmer),
            IntentHandlers.SynopsisHandler(stemmer),
            IntentHandlers.DirectorHandler(stemmer),
            IntentHandlers.ActorHandler(stemmer),
            IntentHandlers.YearHandler(stemmer),
            IntentHandlers.GenreHandler(stemmer),
            IntentHandlers.AwardsHandler(stemmer),
            IntentHandlers.CastHandler(stemmer),
            IntentHandlers.SimilarMoviesHandler(stemmer),
            IntentHandlers.ActorFilmographyHandler(stemmer),
            IntentHandlers.ContextualHandler(stemmer),
        ]

    def get_affirmation_handler(self) -> "AffirmationHandler":
        for h in self.handlers:
            if isinstance(h, AffirmationHandler):
                return h

    def classify(self, tokens: List[str], original_text: str = "") -> str:
        """Classifica o intent a partir dos tokens stemizados.

        Para handlers que implementam matches_original() (ex: PersonSearchHandler),
        passa também o texto original preservando a caixa das letras — necessário
        para detectar nomes próprios por capitalização.
        """
        for handler in self.handlers:
            # PersonSearchHandler usa matches_original() para detectar nomes próprios
            if isinstance(handler, IntentHandlers.PersonSearchHandler):
                if original_text and handler.matches_original(original_text):
                    return handler.get_intent_name()
                continue
            if handler.matches(tokens):
                return handler.get_intent_name()
        return "unknown"

    def get_keywords_for_intent(self, intent_name: str) -> List[str]:
        for handler in self.handlers:
            if handler.get_intent_name() == intent_name:
                return handler.get_stemmed_keywords()
        return []