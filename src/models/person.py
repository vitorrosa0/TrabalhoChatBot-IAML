"""
models/person.py
Entidade Pessoa adaptada ao dataset_reconhecimento.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Person:
    id: int
    nome: str
    popularidade: float
    departamento: str  # "Acting", "Directing", "Writing", etc.
    filmes_conhecidos: List[int] = field(default_factory=list)

    @property
    def is_director(self) -> bool:
        return self.departamento.lower() == "directing"

    @property
    def is_actor(self) -> bool:
        return self.departamento.lower() == "acting"