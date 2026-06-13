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
        result = any(word in self._stemmed_keywords for word in tokens)
        return result

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
        # Removidas palavras vagas (\"sobre\", \"fale\", \"conte\") que causavam
        # falsos positivos ao perguntar sobre diretor, elenco etc.
        return ["sinopse", "resumo", "historia", "enredo", "acontecer"]

    def get_intent_name(self):
        return "ask_synopsis"


class DirectorHandler(IntentHandler):
    def _raw_keywords(self):
        return [
            "diretor", "dirigir", "direcao", "comandou",
            # Removido "fez" e "outro" — são ambíguos.
            "dirigiu", "lista",
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
        # Removidas "ator" e "atriz" — estavam causando conflito com ActorHandler
        # e ask_cast. Agora só dispara quando o usuário usa termos de filmografia.
        # Removido "filme" e "filmes" - estavam causando falso positivo em todas as queries.
        return [
            "outros", "participou", "estrelou", "atuou", "filmografia",
            "trabalhos", "fez", "fizeram", "participacoes", "atuacoes"
        ]

    def get_intent_name(self):
        return "ask_actor_filmography"

class YearHandler(IntentHandler):
    def _raw_keywords(self):
        return ["ano", "lancamento", "lancou", "estreou", "lançado"]

    def get_intent_name(self):
        return "ask_year"

class GenreHandler(IntentHandler):
    def _raw_keywords(self):
        # Removidas "estilo" e "jeito" — estavam conflitando com DirectorHandler
        # (que também usa essas palavras e aparece antes no classifier).
        # "Qual o estilo do filme?" agora vai para DirectorHandler, que trata
        # o contexto corretamente via context.last_topic.
        return ["genero", "tipo", "categoria", "classificacao"]

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
        return ["ela", "mais", "outro"]

    def get_intent_name(self):
        return "contextual_followup"

class GenreSearchHandler(IntentHandler):
    def _raw_keywords(self):
        return [
            "acao", "comedia", "drama", "terror", "suspense",
            "romance", "animacao", "ficcao", "aventura", "thriller"
        ]

    def get_intent_name(self):
        return "ask_genre_search"

class CountrySearchHandler(IntentHandler):
    def _raw_keywords(self):
        return [
            "brasileiro", "brasileira", "brasil",
            "americano", "americana",
            "frances", "francesa",
            "italiano", "italiana",
            "espanhol", "espanhola",
            "coreano", "coreana",
            "japones", "japonesa",
        ]

    def get_intent_name(self):
        return "ask_country_search"


class PersonSearchHandler(IntentHandler):
    """Detecta pedidos de busca por filmografia de ator ou diretor.

    Exemplos de frases que ativam:
        "gostaria de um filme do Tom Holland"
        "filmes com a Isis Valverde"
        "o que o Christopher Nolan dirigiu"
        "filmografia da Fernanda Torres"
        "quais filmes a Meryl Streep fez"

    Nota: o método matches() padrão sempre retorna False.
    O IntentClassifier chama matches_original() com o texto original
    (caixa preservada) para detectar nomes próprios pela capitalização.
    """

    PREP_PATTERNS = {"do", "da", "dos", "das", "pelo", "pela", "com", "de", "sobre", "o", "a"}
    TRIGGER_VERBS = {"filmografia", "participou", "estrelou", "atuou",
                     "fez", "dirigiu", "trabalhos", "atuacoes"}

    def _raw_keywords(self) -> List[str]:
        return ["filmografia", "participou", "estrelou", "atuou"]

    def matches(self, tokens: List[str]) -> bool:
        # Desabilitado: a lógica real está em matches_original()
        return False

    def matches_original(self, original_text: str) -> bool:
        """Recebe o texto original (caixa preservada) para detectar nomes próprios."""
        import re
        text_clean = re.sub(r'[^\w\s]', ' ', original_text).strip()
        words = text_clean.split()
        if not words:
            return False
        words_lower = [w.lower() for w in words]

        # Gatilho 1: "filmografia" sempre indica busca por pessoa
        if "filmografia" in words_lower:
            return True

        # Gatilho 2: "filme(s)" + preposição + palavra com inicial maiúscula
        has_filme = any(w in words_lower for w in ["filme", "filmes"])
        if has_filme:
            for i, word_l in enumerate(words_lower):
                if word_l in self.PREP_PATTERNS and i + 1 < len(words):
                    next_word = words[i + 1]
                    if next_word and next_word[0].isupper():
                        return True

        # Gatilho 3: verbo de ação + nome próprio (ex: "o que Tom Hanks fez")
        has_trigger = any(w in words_lower for w in self.TRIGGER_VERBS)
        if has_trigger:
            for word in words[1:]:
                if word and word[0].isupper():
                    return True

        return False

    def get_intent_name(self) -> str:
        return "ask_person_search"