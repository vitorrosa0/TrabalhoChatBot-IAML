"""
models/movie.py
Entidade Filme adaptada ao dataset_reconhecimento.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Movie:
    id: int
    titulo: str
    titulo_original: str
    generos: List[str]
    ano: str
    origem: List[str] = field(default_factory=list)

    # campos opcionais que podem existir em versões enriquecidas
    sinopse: str = ""
    avaliacao: float = 0.0
    diretor: str = ""
    elenco: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "titulo_original": self.titulo_original,
            "generos": self.generos,
            "ano": self.ano,
            "origem": self.origem,
            "sinopse": self.sinopse,
            "avaliacao": self.avaliacao,
            "diretor": self.diretor,
            "elenco": self.elenco,
        }