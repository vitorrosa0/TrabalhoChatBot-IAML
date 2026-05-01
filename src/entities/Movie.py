from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Movie:
    title: str
    year: int
    genre: List[str]
    synopsis: str
    trivia: List[str]
    awards: Dict[str, int]
    director_name: str