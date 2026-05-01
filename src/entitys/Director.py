from dataclasses import dataclass
from typing import List

@dataclass
class Director:
    name: str
    biography: str
    filmography: List[str]
    style: str