import random
from typing import Tuple, Optional

class ResponseEnricher:
    HOOKS = {
        "ask_year": [
            " Quer saber uma curiosidade sobre a produção?",
            " Quer conhecer o elenco ou a sinopse do filme?",
            " Quer saber mais sobre o diretor que o fez?",
        ],
        "ask_synopsis": [
            " Quer saber quem dirigiu esse filme?",
            " Quer conhecer algumas curiosidades da produção?",
            " Quer conhecer o elenco principal?",
        ],
        "ask_director": [
            " Quer ver outros filmes que ele dirigiu?",
            " Quer saber mais sobre o estilo dele?",
            " Quer conhecer a filmografia completa dele?",
        ],
        "ask_cast": [
            " Quer saber sobre os prêmios que o filme recebeu?",
            " Quer saber uma curiosidade dos bastidores?",
            " Quer conhecer a sinopse e entender melhor os personagens?",
        ],
        "ask_awards": [
            " Quer saber alguma curiosidade dos bastidores?",
            " Quer saber mais sobre como o filme foi produzido?",
            " Quer conhecer o elenco por trás dessa produção?",
        ],
        "ask_similar": [
            " Quer saber mais sobre algum deles?",
            " Quer explorar mais sobre esse filme antes de partir para outro?",
            " Quer conhecer as curiosidades desse aqui antes?",
        ],
        "ask_genre": [
            " Quer conhecer a sinopse do filme?",
            " Quer saber mais sobre o diretor?",
            " Quer saber uma curiosidade sobre como esse estilo foi desenvolvido?",
        ],
        "ask_trivia": [
            " Quer ouvir outra curiosidade?",
            " Quer saber sobre os prêmios que o filme recebeu?",
            " Quer explorar mais sobre o diretor?",
        ],
    }

    HOOK_INTENT_MAP = {
        "ask_synopsis":  "ask_director",
        "ask_director":  "ask_trivia",
        "ask_trivia":    "ask_trivia",
        "ask_awards":    "ask_trivia",
        "ask_cast":      "ask_awards",
        "ask_year":      "ask_trivia",
        "ask_genre":     "ask_synopsis",
        "ask_similar":   "ask_trivia",
    }

    def enrich(self, intent: str, base_response: str, movie) -> Tuple[str, Optional[str]]:
        hooks = self.HOOKS.get(intent)
        if not hooks:
            return base_response, None
        hook_intent = self.HOOK_INTENT_MAP.get(intent)
        return base_response + "\n\n" + random.choice(hooks), hook_intent