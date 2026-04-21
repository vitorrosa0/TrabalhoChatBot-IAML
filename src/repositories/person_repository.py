"""
repositories/person_repository.py
"""
import json
from typing import List, Optional
from ..models.person import Person


class PersonRepository:
    def __init__(self, data_path: str):
        self._people: List[Person] = self._load(data_path)

    def _load(self, path: str) -> List[Person]:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        people = []
        for item in raw.get("pessoas", []):
            people.append(Person(
                id=item.get("id", 0),
                nome=item.get("nome", ""),
                popularidade=float(item.get("popularidade", 0.0)),
                departamento=item.get("departamento") or "Acting",
                filmes_conhecidos=item.get("filmes_conhecidos", []),
            ))
        return people

    def find_all(self) -> List[Person]:
        return list(self._people)

    def find_by_name(self, name: str) -> Optional[Person]:
        name_lower = name.lower()
        return next((p for p in self._people if name_lower in p.nome.lower()), None)

    def find_directors(self) -> List[Person]:
        return [p for p in self._people if p.is_director]

    def find_actors(self) -> List[Person]:
        return [p for p in self._people if p.is_actor]

    def find_by_department(self, department: str) -> List[Person]:
        return [p for p in self._people if p.departamento.lower() == department.lower()]

    def find_most_popular(self, limit: int = 5) -> List[Person]:
        return sorted(self._people, key=lambda p: p.popularidade, reverse=True)[:limit]

    def find_most_popular_directors(self, limit: int = 5) -> List[Person]:
        directors = self.find_directors()
        return sorted(directors, key=lambda p: p.popularidade, reverse=True)[:limit]

    def find_most_popular_actors(self, limit: int = 5) -> List[Person]:
        actors = self.find_actors()
        return sorted(actors, key=lambda p: p.popularidade, reverse=True)[:limit]