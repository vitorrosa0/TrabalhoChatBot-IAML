"""
repositories/lexicon_repository.py
Mapeia termos coloquiais para códigos de país ISO.
Lê a estrutura real do dataset_reconhecimento:
  paises_lexico.codigo_para_termos  →  { "BR": ["brasileiro", ...] }
  paises_lexico.codigo_para_rotulo  →  { "BR": "brasileiros" }
Responsabilidade única: resolução de léxico geográfico.
"""
import json
from typing import Optional


class LexiconRepository:
    def __init__(self, data_path: str):
        raw = self._load(data_path)
        lexico = raw.get("paises_lexico", {})

        # { "BR": ["brasileiro", ...] }
        self._codigo_para_termos: dict = lexico.get("codigo_para_termos", {})

        # { "BR": "brasileiros" }
        self._codigo_para_rotulo: dict = lexico.get("codigo_para_rotulo", {})

        # índice invertido: "brasileiro" -> "BR"
        self._term_map: dict[str, str] = {}
        for code, terms in self._codigo_para_termos.items():
            for term in terms:
                self._term_map[term.lower()] = code

    def _load(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_country(self, text: str) -> Optional[str]:
        """Retorna o código ISO se algum termo do léxico for encontrado no texto."""
        text_lower = text.lower()
        for term, code in self._term_map.items():
            if term in text_lower:
                return code
        return None

    def get_country_label(self, code: str) -> str:
        """Retorna o rótulo plural do país: 'BR' -> 'brasileiros'."""
        return self._codigo_para_rotulo.get(code.upper(), code)

    def all_codes(self) -> list:
        return list(self._codigo_para_termos.keys())