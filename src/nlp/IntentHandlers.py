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

    def get_stemmed_keywords(self) -> List[str]:
        return self._stemmed_keywords

    @abstractmethod
    def get_intent_name(self) -> str:
        pass


class TriviaHandler(IntentHandler):
    def _raw_keywords(self):
        return ["curiosidade", "trivia", "fato", "interessante"]

    def get_intent_name(self):
        return "ask_trivia"


class SynopsisHandler(IntentHandler):
    def _raw_keywords(self):
        return ["sinopse", "resumo", "historia", "enredo", "acontecer", "falar", "contar", "fale", "conte", "fale sobre", "fala sobre", "conta sobre", "conte sobre", "sobre"]

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
        return ["ator", "atriz", "atua", "personagem", "trabalhar"]

    def get_intent_name(self):
        return "ask_actor"


class ActorFilmographyHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ator", "atriz", "outros", "participou", "estrelou", "atuou", "filmografia"]

    def get_intent_name(self):
        return "ask_actor_filmography"

class YearHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ano", "lancamento", "lancou", "estreou", "lançado"]

    def get_intent_name(self):
        return "ask_year"

class GenreHandler(IntentHandler):
    def _raw_keywords(self):
        return [
            "genero", "tipo", "categoria", "classificacao",
            "estilo", "jeito",
        ]

    def get_intent_name(self):
        return "ask_genre"
    
class AwardsHandler(IntentHandler):
    def _raw_keywords(self):
        return ["premio", "premios", "prêmios", "oscar", "ganhou", "venceu", "indicacao", "awards"]

    def get_intent_name(self):
        return "ask_awards"
    
class CastHandler(IntentHandler):
    def _raw_keywords(self):
        return ["elenco", "papel", "interpreta", "cast"]

    def get_intent_name(self):
        return "ask_cast"
    
class SimilarMoviesHandler(IntentHandler):
    def _raw_keywords(self):
        return ["similar", "parecido", "parecidos", "semelhante", "recomenda", "igual"]

    def get_intent_name(self):
        return "ask_similar"

class ContextualHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ele", "ela", "mais", "outro"]

    def get_intent_name(self):
        return "contextual_followup"