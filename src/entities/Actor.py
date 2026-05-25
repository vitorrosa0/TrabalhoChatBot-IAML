from dataclasses import dataclass, field
from typing import List

@dataclass
class Actor:
    name: str
    role: str
    biography: str
    filmography: List[str] = field(default_factory=list)