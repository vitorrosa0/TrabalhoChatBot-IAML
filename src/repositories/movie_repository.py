"""
repositories/movie_repository.py
Acesso aos filmes do dataset_reconhecimento via padrão Repository.
Responsabilidade única: leitura e filtragem de filmes.
"""
import json
import random
from typing import List, Optional
from src.models.movie import Movie


class MovieRepository:
    def __init__(self, data_path: str):
        self._data_path = data_path
        self._movies: List[Movie] = self._load()

    def _load(self) -> List[Movie]:
        with open(self._data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        movies = []
        for item in raw.get("filmes", []):
            # constrói apenas com campos que existem no objeto
            movies.append(Movie(
                id=item.get("id", 0),
                titulo=item.get("titulo", ""),
                titulo_original=item.get("titulo_original", ""),
                generos=item.get("generos", []),
                ano=str(item.get("ano", "")),
                origem=item.get("origem", []),
                sinopse=item.get("sinopse", ""),
                avaliacao=float(item.get("avaliacao", 0.0)),
                diretor=item.get("diretor", ""),
                elenco=item.get("elenco", []),
            ))
        return movies

    def find_all(self) -> List[Movie]:
        return list(self._movies)

    def find_by_id(self, movie_id: int) -> Optional[Movie]:
        return next((m for m in self._movies if m.id == movie_id), None)

    def find_by_country(self, country_code: str) -> List[Movie]:
        code = country_code.upper()
        return [m for m in self._movies if code in [o.upper() for o in m.origem]]

    def find_by_genre(self, genre_slug: str) -> List[Movie]:
        """genre_slug no formato do dataset: 'acao', 'ficcao_cientifica', etc."""
        return [m for m in self._movies if genre_slug.lower() in m.generos]

    def find_by_multiple_genres(self, genre_slugs: List[str]) -> List[Movie]:
        slugs = [g.lower() for g in genre_slugs]
        return [m for m in self._movies if any(g in slugs for g in m.generos)]

    def find_by_director(self, director_name: str) -> List[Movie]:
        name_lower = director_name.lower()
        return [m for m in self._movies if name_lower in m.diretor.lower()]

    def find_by_title(self, title: str) -> Optional[Movie]:
        title_lower = title.lower()
        return next(
            (m for m in self._movies
             if title_lower in m.titulo.lower() or title_lower in m.titulo_original.lower()),
            None
        )

    def find_top_rated(self, limit: int = 5) -> List[Movie]:
        with_rating = [m for m in self._movies if m.avaliacao > 0]
        return sorted(with_rating, key=lambda m: m.avaliacao, reverse=True)[:limit]

    def find_random(self, count: int = 3) -> List[Movie]:
        return random.sample(self._movies, min(count, len(self._movies)))

    def find_by_year(self, year: str) -> List[Movie]:
        return [m for m in self._movies if m.ano == year]

    def find_by_decade(self, decade_start: int) -> List[Movie]:
        return [
            m for m in self._movies
            if m.ano.isdigit() and decade_start <= int(m.ano) < decade_start + 10
        ]

    def search_by_text(self, text: str) -> List[Movie]:
        """Busca simples por substring em título e título original."""
        text_lower = text.lower()
        return [
            m for m in self._movies
            if text_lower in m.titulo.lower() or text_lower in m.titulo_original.lower()
        ]