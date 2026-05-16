import re
from difflib import SequenceMatcher
from typing import Dict
from typing import Dict, Optional

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


class EntityExtractor:
    MATCH_THRESHOLD = 0.82  # ajuste se quiser mais ou menos tolerância

    def __init__(self, repository):
        self.repository = repository
        self.movies = []
        self.directors = []
        self.actors = []
        self._load_entities()

    def _load_entities(self):
        """Carrega todas as entidades do repositório, sem nomes fixos no código."""
        for movie in self.repository.get_all_movies():
            title_lower = movie.title.lower()
            if title_lower not in self.movies:
                self.movies.append(title_lower)

            for actor in movie.cast:
                actor_lower = actor.name.lower()
                if actor_lower not in self.actors:
                    self.actors.append(actor_lower)

        for director in self.repository.get_all_directors():
            director_lower = director.name.lower()
            if director_lower not in self.directors:
                self.directors.append(director_lower)

    def _find_in_text(self, text_lower: str, candidates: list) -> Optional[str]:
        """
        Tenta encontrar um candidato no texto de duas formas:
        1. Substring exata (rápido e preciso)
        2. Similaridade por janela deslizante (tolera erros de digitação)
        """
        for candidate in candidates:
            # 1. Busca exata
            if candidate in text_lower:
                return candidate

            # 2. Busca aproximada — divide o candidato em palavras e
            #    compara com janelas de mesmo tamanho no texto
            cand_words = candidate.split()
            text_words = text_lower.split()
            n = len(cand_words)

            for i in range(len(text_words) - n + 1):
                window = " ".join(text_words[i:i + n])
                if _similarity(window, candidate) >= self.MATCH_THRESHOLD:
                    return candidate

        return None

    def extract(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()
        entities = {}

        match = self._find_in_text(text_lower, self.movies)
        if match:
            entities["movie"] = match

        match = self._find_in_text(text_lower, self.directors + self.actors)
        if match:
            entities["person"] = match

        return entities, text