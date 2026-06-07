from re import search

import requests
from typing import Optional, List
from entities import Movie, Actor, Director
from IMovieRepository import IMovieRepository

TMDB_BASE_URL = "https://api.themoviedb.org/3"

GENRE_MAP = {
    "acao":    28,
    "comedia": 35,
    "drama":   18,
    "terror":  27,
    "suspense": 53,
    "romance": 10749,
    "animacao": 16,
    "ficcao":  878,
    "aventura": 12,
    "thriller": 53,
}

COUNTRY_MAP = {
    "brasileiro": "BR",
    "americano": "US",
    "frances": "FR",
    "italiano": "IT",
    "espanhol": "ES",
    "coreano": "KR",
    "japones": "JP",
}

class TMDBRepository(IMovieRepository):
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._cache: dict = {}
        self._consultado_neste_turno: bool = False

    def reset_turno(self):
        """Reseta o flag a cada novo turno da conversa."""
        self._consultado_neste_turno = False

    def foi_consultado(self) -> bool:
        """Retorna True se a API foi chamada neste turno."""
        return self._consultado_neste_turno
    

    def _get(self, endpoint: str, params: dict = {}) -> Optional[dict]:
        params = {**params, "api_key": self._api_key, "language": "pt-BR"}
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None



    def _fetch_movie_data(self, title: str) -> Optional[dict]:
        if title in self._cache:
            self._consultado_neste_turno = True  # cache hit — dado ainda é da API
            return self._cache[title]

        # chamada real à API
        self._consultado_neste_turno = True

        # 1. Acha o ID pelo título
        search = self._get("/search/movie", {"query": title})
        if not search or not search.get("results"):
            return None

        result = search["results"][0]
        movie_id = result["id"]

        # 2. Busca detalhes + créditos + similares em UMA única chamada
        details = self._get(f"/movie/{movie_id}", {
            "append_to_response": "credits,similar,external_ids"
        })
        if not details:
            return None

        # 3. Busca filmografia do diretor e do ator principal
        credits = details.get("credits", {})
        director_entry = next(
            (p for p in credits.get("crew", []) if p["job"] == "Director"), None
        )
        director_movies = []
        director_bio = ""
        if director_entry:
            director_id = director_entry["id"]
            person_data = self._get(f"/person/{director_id}")
            director_bio = (person_data or {}).get("biography", "") or ""
            dir_credits = self._get(f"/person/{director_id}/movie_credits")
            if dir_credits:
                director_movies = [
                    m["title"]
                    for m in dir_credits.get("crew", [])
                    if m.get("job") == "Director"
                    and m.get("title") != details.get("title")
                    and m.get("vote_count", 0) > 50
                ][:6]

        # 4. Filmografia do ator principal (top billing)
        main_actor_movies = []
        main_actor = credits.get("cast", [None])[0] if credits.get("cast") else None
        if main_actor:
            actor_id = main_actor["id"]
            actor_credits = self._get(f"/person/{actor_id}/movie_credits")
            if actor_credits:
                main_actor_movies = [
                    m["title"]
                    for m in sorted(
                        actor_credits.get("cast", []),
                        key=lambda x: x.get("vote_count", 0),
                        reverse=True
                    )
                    if m.get("title") != details.get("title")
                ][:6]

        # 5. IMDb ID para trivia
        imdb_id = details.get("external_ids", {}).get("imdb_id", "")

        data = {
            "details": details,
            "director_bio": director_bio,
            "director_movies": director_movies,
            "main_actor_movies": main_actor_movies,
            "imdb_id": imdb_id,
        }
        self._cache[title] = data
        return data

    # ------------------------------------------------------------------
    # Conversores: dict TMDB → entidades do projeto
    # ------------------------------------------------------------------

    def _build_movie(self, data: dict) -> Movie:
        details = data["details"]
        credits = details.get("credits", {})
        similar = details.get("similar", {})
        main_actor_movies = data.get("main_actor_movies", [])
        imdb_id = data.get("imdb_id", "")

        # Diretor
        director_name = next(
            (p["name"] for p in credits.get("crew", []) if p["job"] == "Director"),
            "Desconhecido",
        )

        # Elenco top 5
        cast = [
            Actor(
                name=a["name"],
                role=a.get("character", ""),
                biography="",
                filmography=main_actor_movies if i == 0 else [],
            )
            for i, a in enumerate(credits.get("cast", [])[:5])
        ]

        genres = [g["name"] for g in details.get("genres", [])]

        similar_titles = [
            m["title"] for m in similar.get("results", [])[:5]
        ]

        # Trivia: tagline + rating IMDb como curiosidade
        trivia = []
        if details.get("tagline"):
            trivia.append(f'Tagline original: "{details["tagline"]}"')
        if details.get("vote_average"):
            trivia.append(
                f"Nota no TMDB: {round(details['vote_average'], 1)}/10 "
                f"({details.get('vote_count', 0):,} votos)"
            )
        if details.get("budget", 0) > 0:
            trivia.append(f"Orçamento: US$ {details['budget']:,.0f}")
        if details.get("revenue", 0) > 0:
            trivia.append(f"Bilheteria mundial: US$ {details['revenue']:,.0f}")
        # if imdb_id:
        #     trivia.append(f"IMDb ID: {imdb_id} — confira em imdb.com/title/{imdb_id}")

        # Prêmios: TMDB não expõe Oscar — usamos vote_average como indicador
        awards = {}
        if details.get("vote_average", 0) >= 8.0:
            awards["nota_tmdb"] = round(details["vote_average"], 1)

        return Movie(
            title=details.get("title", ""),
            year=int((details.get("release_date") or "0000")[:4]),
            genre=genres,
            synopsis=details.get("overview", ""),
            trivia=trivia,
            awards=awards,
            director_name=director_name,
            cast=cast,
            similar_movies=similar_titles,
        )

    def _build_director(self, data: dict) -> Director:
        credits = data["details"].get("credits", {})
        director_entry = next(
            (p for p in credits.get("crew", []) if p["job"] == "Director"), None
        )
        if not director_entry:
            return None

        return Director(
            name=director_entry["name"],
            biography=data.get("director_bio", "") or "Biografia não disponível.",
            filmography=data.get("director_movies", []),
            style="",
        )

    # ------------------------------------------------------------------
    # Contrato IMovieRepository
    # ------------------------------------------------------------------

    def get_movie_by_title(self, title: str) -> Optional[Movie]:
        data = self._fetch_movie_data(title)
        return self._build_movie(data) if data else None

    def get_director_by_name(self, name: str) -> Optional[Director]:
        for data in self._cache.values():
            credits = data["details"].get("credits", {})
            match = next(
                (p for p in credits.get("crew", [])
                 if p["job"] == "Director" and name.lower() in p["name"].lower()),
                None,
            )
            if match:
                return self._build_director(data)
        return None

    def get_similar_movies(self, title: str = None) -> List[str]:
        if not title:
            return []
        data = self._fetch_movie_data(title)
        if not data:
            return []
        similar = data["details"].get("similar", {})
        return [m["title"] for m in similar.get("results", [])[:5]]

    def get_all_movies(self) -> List[Movie]:
        return [self._build_movie(data) for data in self._cache.values()]

    def get_all_directors(self) -> List[Director]:
        return [d for d in (self._build_director(data) for data in self._cache.values()) if d]
    
    def get_movies_by_genre(self, genre_keyword: str) -> List[tuple]:
        genre_id = GENRE_MAP.get(genre_keyword)
        if not genre_id:
            return []
        result = self._get("/discover/movie", {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": "pt-BR",
            "page": 1,
            "vote_count.gte": 500,
        })
        if not result or not result.get("results"):
            return []
        
        filmes = []
        for m in result["results"]:
            titulo = m["title"]
            ano = m.get("release_date", "")[:4]

            if titulo.isascii() or all(ord(c) < 1000 for c in titulo):
                filmes.append((titulo, ano))
            if len(filmes) == 5:
                break
        
        return filmes
    
    def get_movies_by_country(self, country_keyword: str) -> List[tuple]:
        country_code = COUNTRY_MAP.get(country_keyword)
        if not country_code:
            return []
        result = self._get("/discover/movie", {
            "with_origin_country": country_code,
            "sort_by": "popularity.desc",
            "language": "pt-BR",
            "page": 1,
            "vote_count.gte": 100,
        })
        if not result or not result.get("results"):
            return []
        
        filmes = []
        for m in result["results"]:
            titulo = m["title"]
            ano = m.get("release_date", "")[:4]
            if titulo.isascii() or all(ord(c) < 1000 for c in titulo):
                filmes.append((titulo, ano))
            if len(filmes) == 5:
                break
        return filmes