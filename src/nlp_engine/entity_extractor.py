"""
nlp_engine/entity_extractor.py
"""
import re
from typing import Optional, List

GENRE_MAP = {
    "ação": "acao", "acao": "acao", "aventura": "aventura",
    "drama": "drama", "comédia": "comedia", "comedia": "comedia",
    "terror": "terror", "horror": "terror", "thriller": "suspense",
    "suspense": "suspense", "romance": "romance",
    "ficção científica": "ficcao_cientifica", "ficcao cientifica": "ficcao_cientifica",
    "sci-fi": "ficcao_cientifica", "scifi": "ficcao_cientifica",
    "ficção": "ficcao_cientifica", "crime": "crime",
    "animação": "animacao", "animacao": "animacao", "anime": "animacao",
    "documentário": "documentario", "documentario": "documentario",
    "musical": "musical", "faroeste": "faroeste", "western": "faroeste",
    "fantasia": "fantasia", "guerra": "guerra",
    "história": "historia", "historia": "historia",
    "mistério": "misterio", "misterio": "misterio",
    "biografia": "biografia", "família": "familia", "familia": "familia",
}

SLUG_LABELS = {
    "acao": "Ação", "aventura": "Aventura", "drama": "Drama",
    "comedia": "Comédia", "terror": "Terror", "suspense": "Suspense/Thriller",
    "romance": "Romance", "ficcao_cientifica": "Ficção Científica",
    "crime": "Crime", "animacao": "Animação", "documentario": "Documentário",
    "musical": "Musical", "faroeste": "Faroeste", "fantasia": "Fantasia",
    "guerra": "Guerra", "historia": "História", "misterio": "Mistério",
    "biografia": "Biografia", "familia": "Família",
}


class EntityExtractor:
    def __init__(self, known_people: List[str] = None):
        """
        known_people: lista de nomes carregada do repositório de pessoas.
        Ordena por comprimento decrescente para evitar matches parciais.
        """
        self._known_people: List[str] = sorted(
            [n.lower() for n in (known_people or [])],
            key=len,
            reverse=True
        )

    def extract_genre(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for term, slug in GENRE_MAP.items():
            if term in text_lower:
                return slug
        return None

    def extract_genres(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for term, slug in GENRE_MAP.items():
            if term in text_lower and slug not in found:
                found.append(slug)
        return found

    def extract_person_name(self, text: str) -> Optional[str]:
        """
        Busca nomes do dataset no texto.
        Tenta match por nome completo primeiro, depois por sobrenome.
        """
        text_lower = text.lower()

        # 1. tenta nome completo
        for name in self._known_people:
            if name in text_lower:
                return name.title()

        # 2. tenta match por sobrenome (última palavra do nome)
        for name in self._known_people:
            parts = name.split()
            if len(parts) > 1:
                last_name = parts[-1]
                # só aceita sobrenome se tiver mais de 3 letras (evita falsos positivos)
                if len(last_name) > 3 and last_name in text_lower:
                    return name.title()

        return None

    def extract_movie_title(self, text: str, known_titles: List[str]) -> Optional[str]:
        text_lower = text.lower()
        for title in known_titles:
            if title.lower() in text_lower:
                return title
        return None

    def extract_year(self, text: str) -> Optional[str]:
        match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', text)
        return match.group(1) if match else None

    def slug_to_label(self, slug: str) -> str:
        return SLUG_LABELS.get(slug, slug.replace("_", " ").title())