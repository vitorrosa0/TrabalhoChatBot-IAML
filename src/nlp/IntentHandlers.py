from abc import ABC, abstractmethod
from typing import List
from nltk.stem import RSLPStemmer

class IntentHandler(ABC):
    def __init__(self, stemmer: RSLPStemmer):
        self._stemmer = stemmer
        self._stemmed_keywords = [
            stemmer.stem(kw) for kw in self._raw_keywords()
        ]

    def _raw_keywords(self) -> List[str]:
        raise NotImplementedError

    def matches(self, tokens: List[str]) -> bool:
        return any(word in self._stemmed_keywords for word in tokens)

    @abstractmethod
    def get_intent_name(self) -> str:
        pass


class SynopsisHandler(IntentHandler):
    def _raw_keywords(self):
        return ["sinopse", "resumo", "historia", "enredo", "acontecer"]

    def get_intent_name(self):
        return "ask_synopsis"


class DirectorHandler(IntentHandler):
    def _raw_keywords(self):
        return [
            "diretor", "dirigir", "direcao", "comandou",
            "outro", "fez", "dirigiu", "lista",
            "estilo", "jeito", "caracteristica",
        ]

    def get_intent_name(self):
        return "ask_director"


class ActorHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ator", "atriz", "elenco", "atua", "personagem", "trabalhar"]

    def get_intent_name(self):
        return "ask_actor"


class TriviaHandler(IntentHandler):
    def _raw_keywords(self):
        return ["curiosidade", "trivia", "fato", "interessante"]

    def get_intent_name(self):
        return "ask_trivia"

class YearHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ano", "lancamento", "lancou", "estreou", "quando", "lançado"]

    def get_intent_name(self):
        return "ask_year"

class GenreHandler(IntentHandler):
    def _raw_keywords(self):
        return ["genero", "tipo", "categoria", "estilo", "classificacao"]

    def get_intent_name(self):
        return "ask_genre"


class ContextualHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ele", "ela", "quem", "mais", "outro"]

    def get_intent_name(self):
        return "contextual_followup"