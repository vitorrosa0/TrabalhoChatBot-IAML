import re
from difflib import SequenceMatcher
from typing import Dict, Optional, List

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


class EntityExtractor:
    MATCH_THRESHOLD = 0.82

    def __init__(self, repository):
        self.repository = repository
        self.movies = []
        self.directors = []
        self.actors = []
        self._load_entities()

    def _load_entities(self):
        """Pré-carrega entidades já no cache do repositório (útil para LocalJsonRepository)."""
        for movie in self.repository.get_all_movies():
            self._register_movie(movie)

        for director in self.repository.get_all_directors():
            director_lower = director.name.lower()
            if director_lower not in self.directors:
                self.directors.append(director_lower)

    def _register_movie(self, movie):
        """Registra um filme e seu elenco na lista local."""
        title_lower = movie.title.lower()
        if title_lower not in self.movies:
            self.movies.append(title_lower)
        for actor in movie.cast:
            actor_lower = actor.name.lower()
            if actor_lower not in self.actors:
                self.actors.append(actor_lower)

    def _find_in_text(self, text_lower: str, candidates: list) -> Optional[str]:
        """Busca exata primeiro, depois aproximada por janela deslizante."""
        for candidate in candidates:
            if candidate in text_lower:
                return candidate

            cand_words = candidate.split()
            text_words = text_lower.split()
            n = len(cand_words)
            for i in range(len(text_words) - n + 1):
                window = " ".join(text_words[i:i + n])
                if _similarity(window, candidate) >= self.MATCH_THRESHOLD:
                    return candidate

        return None

    def _extract_candidate_titles(self, text_lower: str):
        """
        Gera candidatos a título de filme a partir do texto,
        removendo stopwords e tentando janelas de 1 a 4 palavras.
        """
        words = [w for w in text_lower.split() if len(w) > 2]
        candidates = []
        for size in range(4, 0, -1):  # tenta frases maiores primeiro
            for i in range(len(words) - size + 1):
                candidates.append(" ".join(words[i:i + size]))
        return candidates

    def _try_fetch_from_api(self, text_lower: str) -> Optional[str]:
        """
        Quando a lista local está vazia ou não houve match,
        tenta buscar o filme diretamente no repositório usando
        candidatos extraídos do texto.
        """
        for candidate in self._extract_candidate_titles(text_lower):
            movie = self.repository.get_movie_by_title(candidate)
            if movie:
                self._register_movie(movie)
                return movie.title.lower()
        return None

    def extract(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()
        entities = {}

        # 1. Tenta encontrar na lista local (já conhecidos)
        match = self._find_in_text(text_lower, self.movies)

        # 2. Se não achou, vai na API buscar pelo texto
        if not match:
            match = self._try_fetch_from_api(text_lower)

        if match:
            entities["movie"] = match

        # Pessoas: só busca na lista local (já populada após busca de filme)
        match = self._find_in_text(text_lower, self.directors + self.actors)
        if match:
            entities["person"] = match

        return entities, text

    def extract_from_tokens(self, filtered_tokens: List[str], original_text: str) -> Dict[str, str]:
        """
        Extrai entidades usando tokens já filtrados pelo intent,
        evitando que keywords de comando sejam confundidas com títulos.
        """

        meaningful_tokens = [t for t in filtered_tokens if len(t) >= 4]
        
        candidates = []
        for size in range(len(meaningful_tokens), 0, -1):
            for i in range(len(meaningful_tokens) - size + 1):
                candidates.append(" ".join(meaningful_tokens[i:i + size]))

        text_lower = original_text.lower()
        entities = {}

        # busca na lista local primeiro
        match = self._find_in_text(" ".join(filtered_tokens), self.movies)

        # se não achou, tenta na API com os candidatos filtrados
        if not match:
            for candidate in candidates:
                movie = self.repository.get_movie_by_title(candidate)
                if movie:
                    self._register_movie(movie)
                    match = movie.title.lower()
                    break

        if match:
            entities["movie"] = match

        # pessoas: busca na lista local
        match = self._find_in_text(text_lower, self.directors + self.actors)
        if match:
            entities["person"] = match

        return entities, original_text
    
    
    def extract_title(self, clean_text: str) -> Optional[str]:
        """
        Busca título usando texto limpo sem stemming.
        Só aceita resultado da API se a similaridade for alta o suficiente.
        """
        # busca exata na lista local
        match = self._find_in_text(clean_text, self.movies)
        if match:
            return match

        # busca na API com candidatos — só aceita match com similaridade alta
        words = clean_text.split()
        candidates = []
        for size in range(len(words), 0, -1):
            # Se clean_text tem 2 ou mais palavras, ignora candidatos de tamanho 1
            if len(words) >= 2 and size == 1:
                continue
            for i in range(len(words) - size + 1):
                candidates.append(" ".join(words[i:i + size]))

        for candidate in candidates:
            movie = self.repository.get_movie_by_title(candidate)
            if movie:
                similarity = _similarity(candidate.lower(), movie.title.lower())
                if similarity >= 0.75:
                    self._register_movie(movie)
                    return movie.title.lower()

        return None

    def extract_person_name(self, text: str) -> Optional[str]:
        """Extrai o nome de uma pessoa (ator/diretor) a partir do texto original.

        Estratégia: busca padrões como 'do/da/com/de/pelo/pela + [Nome Próprio]'
        e retorna a sequência de palavras com inicial maiúscula após a preposição.

        Exemplos:
            "gostaria de um filme do Tom Holland" → "Tom Holland"
            "filmes com a Isis Valverde"          → "Isis Valverde"
            "o que o Christopher Nolan dirigiu"   → "Christopher Nolan"
        """
        import re

        # Normaliza o texto mas preserva caixa para detectar nomes próprios
        text_clean = re.sub(r'[^\w\s]', ' ', text).strip()
        words = text_clean.split()

        PREPOSICOES = {"do", "da", "dos", "das", "com", "de", "pelo", "pela", "sobre", "o", "a"}

        # Percorre as palavras e, ao encontrar uma preposição, coleta as
        # palavras seguintes que comecem com maiúscula (nome próprio)
        name_tokens = []
        collecting = False
        for word in words:
            word_lower = word.lower()
            if word_lower in PREPOSICOES:
                # reinicia coleta após a preposição
                name_tokens = []
                collecting = True
                continue
            if collecting:
                if word[0].isupper():
                    name_tokens.append(word)
                else:
                    # palavra minúscula interrompe o nome (ex: "de um filme")
                    if name_tokens:
                        break
                    # ainda não começamos — continua buscando
        
        if len(name_tokens) >= 1:
            return " ".join(name_tokens)

        # Fallback: procura qualquer sequência de 2+ palavras com inicial maiúscula
        # que não seja a primeira palavra da frase (provável início de frase)
        capitalized_sequence = []
        for i, word in enumerate(words[1:], start=1):
            if word[0].isupper():
                capitalized_sequence.append(word)
            else:
                if len(capitalized_sequence) >= 2:
                    return " ".join(capitalized_sequence)
                capitalized_sequence = []
        if len(capitalized_sequence) >= 2:
            return " ".join(capitalized_sequence)

        return None