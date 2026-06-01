import random
from typing import Tuple, Optional

class ResponseEnricher:
    HOOKS = {
        "ask_year": [
            " Foi um ano marcante para o cinema de ficção científica. Curiosidades sobre a produção te interessam?",
            " Naquela época, o filme surpreendeu muita gente nas salas de cinema. Quer saber como ele foi recebido pela crítica?",
            " Sete anos de desenvolvimento culminaram nesse lançamento. Quer saber uma curiosidade dos bastidores?",
        ],
        "ask_synopsis": [
            " É uma trama que mistura ciência e emoção de forma única. Quer saber quem está por trás dessa direção?",
            " Uma história que deixa muita gente pensando por dias. Quer conhecer algumas curiosidades da produção?",
            " O roteiro levou anos para ser finalizado. Quer saber mais sobre o diretor que trouxe essa história à vida?",
        ],
        "ask_director": [
            " Um diretor que sempre surpreende. Quer ver outros filmes que ele assinou?",
            " Ele é conhecido por não abrir mão de efeitos práticos. Quer saber mais sobre o estilo dele?",
            " Uma das mentes mais criativas do cinema atual. Quer conhecer a filmografia completa dele?",
        ],
        "ask_cast": [
            " O elenco foi muito elogiado pela crítica. Quer saber sobre os prêmios que o filme recebeu?",
            " Cada ator trouxe algo único para o filme. Quer saber uma curiosidade dos bastidores?",
            " Uma escolha de elenco impecável. Quer conhecer a sinopse e entender melhor os personagens?",
        ],
        "ask_awards": [
            " Um reconhecimento justo para um filme tão elaborado. Quer saber alguma curiosidade dos bastidores?",
            " Concorrer ao Oscar é sempre um marco. Quer saber mais sobre como o filme foi produzido?",
            " As indicações refletem o cuidado com cada detalhe. Quer conhecer o elenco por trás dessa produção?",
        ],
        "ask_similar": [
            " São ótimas pedidas se você curtiu esse clima. Quer saber mais sobre algum deles?",
            " Filmes que também desafiam a percepção do espectador. Quer conhecer as curiosidades desse aqui antes?",
            " Cada um tem seu toque único, mas a mesma pegada. Quer explorar mais sobre esse filme antes de partir para outro?",
        ],
        "ask_genre": [
            " Uma combinação que funciona muito bem nesse filme. Quer conhecer a sinopse?",
            " Esse mix de gêneros é uma das marcas registradas do diretor. Quer saber mais sobre ele?",
            " Difícil encaixar em apenas uma categoria. Quer saber uma curiosidade sobre como esse estilo foi desenvolvido?",
        ],
        "ask_trivia": [
            " Os bastidores desse filme são cheios de histórias assim. Quer ouvir outra?",
            " Esse tipo de detalhe mostra o cuidado da produção. Quer saber sobre os prêmios que ele recebeu?",
            " Sempre tem algo surpreendente nesse filme. Quer explorar mais sobre o diretor?",
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
