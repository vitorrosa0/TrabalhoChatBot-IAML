from abc import ABC, abstractmethod
from typing import List


class IntentHandler(ABC):
    @abstractmethod
    def matches(self, tokens: List[str]) -> bool:
        pass

    @abstractmethod
    def get_intent_name(self) -> str:
        pass

class SynopsisHandler(IntentHandler):
    def matches(self, tokens: List[str]) -> bool:
        keywords = ["sinopse", "resumo", "historia", "enredo", "acontecer"]
        return any(word in tokens for word in keywords)

    def get_intent_name(self) -> str:
        return "ask_synopsis"

class DirectorHandler(IntentHandler):
    def matches(self, tokens: List[str]) -> bool:
        keywords = ["diretor", "dirigir", "quem fez", "direcao", "comandou"]
        return any(word in tokens for word in keywords)

    def get_intent_name(self) -> str:
        return "ask_director"

class ActorHandler(IntentHandler):
    def matches(self, tokens: List[str]) -> bool:
        keywords = ["ator", "atriz", "elenco", "atua", "personagem", "trabalhar"]
        return any(word in tokens for word in keywords)

    def get_intent_name(self) -> str:
        return "ask_actor"

class TriviaHandler(IntentHandler):
    def matches(self, tokens: List[str]) -> bool:
        keywords = ["curiosidade", "trivia", "fato", "interessante", "saber mais"]
        return any(word in tokens for word in keywords)

    def get_intent_name(self) -> str:
        return "ask_trivia"


class ContextualHandler(IntentHandler):
    def matches(self, tokens: List[str]) -> bool:
        # Detecta pronomes ou frases de continuação
        continuations = ["ele", "ela", "quem", "mais", "outro"]
        # Removemos a trava de len(tokens) <= 3 para aceitar perguntas maiores
        return any(word in tokens for word in continuations)

    def get_intent_name(self) -> str:
        return "contextual_followup"