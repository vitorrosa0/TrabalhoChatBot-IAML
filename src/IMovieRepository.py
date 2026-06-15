from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple
from entities import Movie, Actor, Director

class IMovieRepository(ABC):
    @abstractmethod
    def get_movie_by_title(self, title: str, year: str = None, lang: str = None) -> Optional[Movie]:
        pass

    @abstractmethod
    def get_director_by_name(self, name: str) -> Optional[Director]:
        pass

    @abstractmethod
    def get_similar_movies(self, title: str = None) -> List[str]:
        pass

    @abstractmethod
    def get_all_movies(self) -> List[Movie]:
        pass

    @abstractmethod
    def get_all_directors(self) -> List[Director]:
        pass

    @abstractmethod
    def reset_turno(self):
        pass

    @abstractmethod
    def foi_consultado(self) -> bool:
        pass

    @abstractmethod
    def get_movies_by_genre(self, genre_keyword: str) -> List[Tuple[str, str]]:
        pass

    @abstractmethod
    def get_movies_by_country(self, country_keyword: str) -> List[Tuple[str, str]]:
        pass

    @abstractmethod
    def search_person_movies(self, name: str) -> List[Tuple[str, str, str]]:
        """Busca filmografia de um ator ou diretor pelo nome.
        Retorna lista de (título, ano, personagem/função)."""
        pass

    @abstractmethod
    def search_movie_suggestions(self, query: str) -> List[Tuple[str, str]]:
        """Retorna sugestões de filmes para um termo de busca genérico.
        Retorna lista de (título, ano)."""
        pass

    @abstractmethod
    def resolve_ambiguous_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Compara popularidade na TMDB para determinar se uma query é Filme ou Pessoa.
        Retorna:
            ("movie", titulo_do_filme)
            ("person", nome_da_pessoa)
            (None, None) se não encontrar nada.
        """
        pass

class LocalJsonRepository(IMovieRepository):
    def __init__(self, data: Dict):
        self._movies: List[Movie] = []
        self._directors: List[Director] = []

        for entry in data["movies"]:
            cast = [Actor(a["name"], a["role"], a["biography"]) for a in entry["cast"]]
            m = entry["movie"]
            d = entry["director"]
            movie = Movie(m["title"], m["year"], m["genre"], m["synopsis"], m["trivia"], m["awards"], d["name"], cast, m.get("similar_movies", []))
            director = Director(d["name"], d["biography"], d["filmography"], d["style"])
            self._movies.append(movie)
            self._directors.append(director)

    def get_movie_by_title(self, title: str, year: str = None, lang: str = None) -> Optional[Movie]:
        for movie in self._movies:
            if title.lower() in movie.title.lower():
                if year and str(movie.year) != str(year):
                    continue
                return movie
        return None

    def get_director_by_name(self, name: str) -> Optional[Director]:
        for director in self._directors:
            if name.lower() in director.name.lower():
                return director
        return None

    def get_similar_movies(self, title: str = None) -> list:
        # Se um título for passado, retorna apenas os similares daquele filme
        if title:
            for movie in self._movies:
                if title.lower() in movie.title.lower():
                    return movie.similar_movies
        # Sem título: retorna todos sem duplicata (fallback)
        seen = set()
        result = []
        for movie in self._movies:
            for s in movie.similar_movies:
                if s not in seen:
                    seen.add(s)
                    result.append(s)
        return result

    def get_all_movies(self) -> List[Movie]:
        return self._movies

    def get_all_directors(self) -> List[Director]:
        return self._directors

    def reset_turno(self):
        pass  # LocalJsonRepository não faz chamadas externas

    def foi_consultado(self) -> bool:
        return False

    def get_movies_by_genre(self, genre_keyword: str) -> List[Tuple[str, str]]:
        return []

    def get_movies_by_country(self, country_keyword: str) -> List[Tuple[str, str]]:
        return []

    def search_person_movies(self, name: str) -> List[Tuple[str, str, str]]:
        return []

    def search_movie_suggestions(self, query: str) -> List[Tuple[str, str]]:
        return []

    def resolve_ambiguous_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        return None, None