"""
nlp_engine/entity_extractor.py
Extrai entidades do texto: gênero (no slug do dataset), título, nome de pessoa.
Responsabilidade única: extração de entidades nomeadas.
"""
import re
from typing import Optional, List

# Mapeia termos naturais -> slug do dataset
GENRE_MAP = {
    "ação": "acao",
    "acao": "acao",
    "aventura": "aventura",
    "drama": "drama",
    "comédia": "comedia",
    "comedia": "comedia",
    "terror": "terror",
    "horror": "terror",
    "thriller": "suspense",
    "suspense": "suspense",
    "romance": "romance",
    "ficção científica": "ficcao_cientifica",
    "ficcao cientifica": "ficcao_cientifica",
    "sci-fi": "ficcao_cientifica",
    "scifi": "ficcao_cientifica",
    "ficção": "ficcao_cientifica",
    "crime": "crime",
    "animação": "animacao",
    "animacao": "animacao",
    "anime": "animacao",
    "documentário": "documentario",
    "documentario": "documentario",
    "musical": "musical",
    "faroeste": "faroeste",
    "western": "faroeste",
    "fantasia": "fantasia",
    "guerra": "guerra",
    "história": "historia",
    "historia": "historia",
    "mistério": "misterio",
    "misterio": "misterio",
    "biografia": "biografia",
    "família": "familia",
    "familia": "familia",
}

# Nomes conhecidos para busca por substring
KNOWN_PEOPLE = [
    "tarantino", "nolan", "coppola", "fincher", "spielberg", "kubrick",
    "scorsese", "lynch", "burton", "hitchcock", "wilder", "ford",
    "meirelles", "padilha", "walter salles", "kleber mendonça",
    "bong joon", "park chan", "wong kar", "akira kurosawa",
    "robert de niro", "al pacino", "meryl streep", "brad pitt",
    "leonardo dicaprio", "tom hanks", "cate blanchett",
    "vincent price", "wagner moura", "fernanda montenegro",
]


class EntityExtractor:

    def extract_genre(self, text: str) -> Optional[str]:
        """Retorna o primeiro slug de gênero encontrado."""
        text_lower = text.lower()
        for term, slug in GENRE_MAP.items():
            if term in text_lower:
                return slug
        return None

    def extract_genres(self, text: str) -> List[str]:
        """Retorna todos os slugs de gênero encontrados (sem duplicatas)."""
        text_lower = text.lower()
        found = []
        for term, slug in GENRE_MAP.items():
            if term in text_lower and slug not in found:
                found.append(slug)
        return found

    def extract_person_name(self, text: str) -> Optional[str]:
        """Retorna o nome/sobrenome de pessoa reconhecido no texto."""
        text_lower = text.lower()
        for name in KNOWN_PEOPLE:
            if name in text_lower:
                return name.title()
        return None

    def extract_movie_title(self, text: str, known_titles: List[str]) -> Optional[str]:
        """
        Busca por títulos conhecidos no texto.
        Recebe a lista de títulos do repositório para não ter estado fixo aqui.
        """
        text_lower = text.lower()
        for title in known_titles:
            if title.lower() in text_lower:
                return title
        return None

    def extract_year(self, text: str) -> Optional[str]:
        """Extrai um ano de 4 dígitos do texto."""
        match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', text)
        return match.group(1) if match else None

    def slug_to_label(self, slug: str) -> str:
        """Converte slug de gênero para label legível."""
        labels = {
            "acao": "Ação",
            "aventura": "Aventura",
            "drama": "Drama",
            "comedia": "Comédia",
            "terror": "Terror",
            "suspense": "Suspense/Thriller",
            "romance": "Romance",
            "ficcao_cientifica": "Ficção Científica",
            "crime": "Crime",
            "animacao": "Animação",
            "documentario": "Documentário",
            "musical": "Musical",
            "faroeste": "Faroeste",
            "fantasia": "Fantasia",
            "guerra": "Guerra",
            "historia": "História",
            "misterio": "Mistério",
            "biografia": "Biografia",
            "familia": "Família",
        }
        return labels.get(slug, slug.replace("_", " ").title())