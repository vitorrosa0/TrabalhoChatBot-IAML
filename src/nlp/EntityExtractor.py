import re
from typing import Dict


class EntityExtractor:
    def __init__(self, repository):
        self.repository = repository
        self.movies = []
        self.directors = []
        self.actors = []

        self._load_entities()

    def _load_entities(self):
        """Carrega dados do repository"""
        movie = self.repository.get_movie_by_title("Interestelar")
        if movie:
            self.movies.append(movie.title.lower())

        director = self.repository.get_director_by_name("Christopher Nolan")
        if director:
            self.directors.append(director.name.lower())

        self.actors.append("matthew mcconaughey")

    def extract(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()
        entities = {}

        for movie in self.movies:
            if movie in text_lower:
                entities["movie"] = movie

        for person in self.directors + self.actors:
            if person in text_lower:
                entities["person"] = person

        return entities, text