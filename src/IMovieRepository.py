from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from entities import Movie, Actor, Director

# Interface abstrata (Contrato)
class IMovieRepository(ABC):
    @abstractmethod
    def get_movie_by_title(self, title: str) -> Optional[Movie]:
        pass

    @abstractmethod
    def get_director_by_name(self, name: str) -> Optional[Director]:
        pass

    @abstractmethod
    def get_similar_movies(self) -> List[str]:
        pass



# Implementação concreta que lê o seu JSON
class LocalJsonRepository(IMovieRepository):
    def __init__(self, data: Dict):
        self._data = data
        self._movie = self._map_movie()
        self._director = self._map_director()
        self._cast = self._map_cast()

    def _map_movie(self) -> Movie:
        m = self._data["movie"]
        d_name = self._data["director"]["name"]
        return Movie(m["title"], m["year"], m["genre"], m["synopsis"], m["trivia"], m["awards"], d_name)

    def _map_director(self) -> Director:
        d = self._data["director"]
        return Director(d["name"], d["biography"], d["filmography"], d["style"])

    def _map_cast(self) -> List[Actor]:
        return [Actor(a["name"], a["role"], a["biography"]) for a in self._data["cast"]]

    # Implementação dos métodos do contrato
    def get_movie_by_title(self, title: str) -> Optional[Movie]:
        if title.lower() in self._movie.title.lower():
            return self._movie
        return None

    def get_director_by_name(self, name: str) -> Optional[Director]:
        if name.lower() in self._director.name.lower():
            return self._director
        return None

    def get_similar_movies(self) -> List[str]:
        return self._data.get("similar_movies", [])