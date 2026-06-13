from typing import Optional, List, Tuple

import requests
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


    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        # Corrigido: não usa dicionário mutável como valor padrão (bug Python clássico)
        if params is None:
            params = {}
        params = {**params, "api_key": self._api_key, "language": "pt-BR"}
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None


    def _fetch_movie_data(self, title: str, year: str = None, lang: str = None) -> Optional[dict]:
        # Normaliza a chave do cache para incluir o ano e idioma (se houver)
        cache_key = f"{title.lower().strip()}_{year or ''}_{lang or ''}"
        if cache_key in self._cache:
            self._consultado_neste_turno = True  # cache hit — dado ainda é da API
            return self._cache[cache_key]

        # chamada real à API
        self._consultado_neste_turno = True

        # 1. Acha o ID pelo título
        params = {"query": title}
        if year:
            params["primary_release_year"] = year
            
        search_result = self._get("/search/movie", params)
        if not search_result or not search_result.get("results"):
            return None

        # Filtra por idioma original se especificado (ex: "brasileiro" -> "pt")
        results = search_result["results"]
        if lang:
            lang_filtered = [r for r in results if r.get("original_language") == lang]
            if lang_filtered:
                results = lang_filtered

        # Tenta encontrar o melhor match: título PT-BR ou título original em inglês
        best_result = self._pick_best_movie_result(results, title)
        if not best_result:
            return None

        movie_id = best_result["id"]
        
        # Coleta alternativas (filmes com título parecido/igual, max 2)
        alternatives = []
        best_title_lower = best_result.get("title", "").lower()
        for r in results:
            if r["id"] == movie_id:
                continue
            r_title = r.get("title", "")
            # Considera alternativa se o nome contiver ou for contido pelo título buscado
            if title.lower() in r_title.lower() or r_title.lower() in title.lower():
                alt_year = (r.get("release_date") or "0000")[:4]
                alternatives.append(f"{r_title} ({alt_year})")
            if len(alternatives) >= 2:
                break

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
            "alternatives": alternatives,
        }
        self._cache[cache_key] = data
        return data

    def _pick_best_movie_result(self, results: list, query: str) -> Optional[dict]:
        """Escolhe o resultado TMDB mais relevante comparando com título PT-BR e título original.
        Isso resolve casos como 'Spider-Man: No Way Home' que em pt-BR retorna
        'Homem-Aranha: Sem Volta Para Casa'."""
        import re
        query_lower = query.lower().strip()
        query_no_article = re.sub(r'^(o|a|os|as)\s+', '', query_lower)

        for result in results:
            title_ptbr = result.get("title", "").lower()
            title_orig = result.get("original_title", "").lower()
            # Match direto (substring em qualquer direção)
            if query_lower in title_ptbr or title_ptbr in query_lower:
                return result
            if query_lower in title_orig or title_orig in query_lower:
                return result
            # Tenta sem o artigo inicial
            if query_no_article in title_ptbr or title_ptbr in query_no_article:
                return result
            if query_no_article in title_orig or title_orig in query_no_article:
                return result

        # Fallback: retorna o primeiro resultado (mais relevante por popularidade)
        return results[0] if results else None

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
            alternatives=data.get("alternatives", []),
        )

    def _build_director(self, data: dict) -> Optional[Director]:
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

    def get_movie_by_title(self, title: str, year: str = None, lang: str = None) -> Optional[Movie]:
        data = self._fetch_movie_data(title, year, lang)
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

    def get_movies_by_genre(self, genre_keyword: str) -> List[Tuple[str, str]]:
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

    def get_movies_by_country(self, country_keyword: str) -> List[Tuple[str, str]]:
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

    def search_person_movies(self, name: str) -> List[Tuple[str, str, str]]:
        """Busca filmografia de um ator ou diretor pelo nome na TMDB.
        Retorna lista de (título, ano, personagem/função).
        Usa match exato de nome para evitar falsos positivos (ex: 'Isis' em título de filme)."""
        self._consultado_neste_turno = True

        result = self._get("/search/person", {"query": name})
        if not result or not result.get("results"):
            return []

        candidates = result["results"]
        # Tenta match exato primeiro, depois substring, depois o mais popular
        person = next(
            (p for p in candidates if p["name"].lower() == name.lower()),
            None
        )
        if not person:
            person = next(
                (p for p in candidates if name.lower() in p["name"].lower()),
                None
            )
        if not person:
            person = candidates[0]

        person_id = person["id"]
        credits = self._get(f"/person/{person_id}/movie_credits")
        if not credits:
            return []

        # Combina filmes como ator e como diretor/crew
        filmes_como_ator = [
            (m["title"], (m.get("release_date") or "")[:4], m.get("character", ""))
            for m in sorted(
                credits.get("cast", []),
                key=lambda x: x.get("vote_count", 0),
                reverse=True
            )
            if m.get("title") and m.get("vote_count", 0) > 50
        ][:8]

        filmes_como_crew = [
            (m["title"], (m.get("release_date") or "")[:4], m.get("job", ""))
            for m in sorted(
                credits.get("crew", []),
                key=lambda x: x.get("vote_count", 0),
                reverse=True
            )
            if m.get("job") == "Director" and m.get("title") and m.get("vote_count", 0) > 50
        ][:5]

        # Se encontrou filmes como diretor, retorna como diretor; senão como ator
        if filmes_como_crew and not filmes_como_ator:
            return filmes_como_crew
        return filmes_como_ator if filmes_como_ator else filmes_como_crew

    def search_movie_suggestions(self, query: str) -> List[Tuple[str, str]]:
        """Retorna sugestões de filmes para um termo de busca genérico.
        Usado para desambiguação ao invés de chamar o LLM."""
        result = self._get("/search/movie", {"query": query})
        if not result or not result.get("results"):
            return []
        return [
            (m["title"], (m.get("release_date") or "")[:4])
            for m in result["results"][:4]
            if m.get("title")
        ]

    def resolve_ambiguous_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Busca na TMDB para determinar se a query é Filme ou Pessoa,
        comparando a popularidade do melhor match.
        """
        self._consultado_neste_turno = True
        
        movie_res = self._get("/search/movie", {"query": query})
        person_res = self._get("/search/person", {"query": query})
        
        best_movie = None
        movie_pop = 0.0
        if movie_res and movie_res.get("results"):
            best_movie = self._pick_best_movie_result(movie_res["results"], query)
            if best_movie:
                movie_pop = best_movie.get("popularity", 0.0)
            
        best_person = None
        person_pop = 0.0
        if person_res and person_res.get("results"):
            # Dá um peso extra se for match exato de nome de pessoa
            candidates = person_res["results"]
            exact_match = next((p for p in candidates if p["name"].lower() == query.lower()), None)
            if exact_match:
                best_person = exact_match
                person_pop = best_person.get("popularity", 0.0) * 1.5 # Bônus de match exato
            else:
                best_person = candidates[0]
                person_pop = best_person.get("popularity", 0.0)
                
        if not best_movie and not best_person:
            return None, None
            
        if movie_pop > person_pop:
            return "movie", best_movie.get("title")
        else:
            return "person", best_person.get("name")