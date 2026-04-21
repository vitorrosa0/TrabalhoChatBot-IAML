import json
from typing import Optional

# Fallback para países não mapeados no dataset
FALLBACK_LABELS = {
    "GB": "britânico", "DE": "alemão", "AU": "australiano",
    "NZ": "neozelandês", "CA": "canadense", "CN": "chinês",
    "RU": "russo", "SE": "sueco", "DK": "dinamarquês",
    "NO": "norueguês", "BE": "belga", "PL": "polonês",
    "LV": "letão", "IE": "irlandês", "AT": "austríaco",
    "CH": "suíço", "PT": "português", "ZA": "sul-africano",
    "HK": "hong-konguês", "TW": "taiwanês", "TH": "tailandês",
    "ID": "indonésio", "PH": "filipino", "TR": "turco",
}

class LexiconRepository:
    def __init__(self, data_path: str):
        raw = self._load(data_path)
        lexico = raw.get("paises_lexico", {})
        self._codigo_para_termos: dict = lexico.get("codigo_para_termos", {})
        self._codigo_para_rotulo: dict = lexico.get("codigo_para_rotulo", {})
        self._term_map: dict[str, str] = {}
        for code, terms in self._codigo_para_termos.items():
            for term in terms:
                self._term_map[term.lower()] = code

    def _load(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_country(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for term, code in self._term_map.items():
            if term in text_lower:
                return code
        return None

    def get_country_label(self, code: str) -> str:
        """Retorna rótulo singular do país para uso em frases."""
        # singular do dataset (ajusta plural para singular)
        rotulo = self._codigo_para_rotulo.get(code.upper(), "")
        if rotulo:
            # converte plural para singular removendo 's' final quando possível
            PLURAL_TO_SINGULAR = {
                "brasileiros": "brasileiro", "americanos": "americano",
                "franceses": "francês", "espanhóis": "espanhol",
                "italianos": "italiano", "japoneses": "japonês",
                "coreanos": "coreano", "mexicanos": "mexicano",
                "argentinos": "argentino", "indianos": "indiano",
                "holandeses": "holandês",
            }
            return PLURAL_TO_SINGULAR.get(rotulo, rotulo)
        # fallback para países não mapeados
        return FALLBACK_LABELS.get(code.upper(), code)

    def get_country_label_plural(self, code: str) -> str:
        """Rótulo plural para listas: 'filmes brasileiros'."""
        return self._codigo_para_rotulo.get(code.upper(),
               FALLBACK_LABELS.get(code.upper(), code))

    def all_codes(self) -> list:
        return list(self._codigo_para_termos.keys())