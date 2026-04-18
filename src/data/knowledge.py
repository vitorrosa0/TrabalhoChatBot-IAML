"""
Resolução de entidades em camadas: cache local (JSON minerado) → API TMDB.
O arquivo ``data/dataset_conhecimento.json`` é opcional; se não existir, cai direto na API.
"""
from __future__ import annotations

import json
import os
from difflib import SequenceMatcher
from typing import Any, Dict, Optional

_JSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "dataset_conhecimento.json")
)
_cache: Optional[Dict[str, Any]] = None


def _carregar() -> Dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    if not os.path.isfile(_JSON_PATH):
        _cache = {"filmes": [], "pessoas": []}
        return _cache
    with open(_JSON_PATH, "r", encoding="utf-8") as f:
        _cache = json.load(f)
    return _cache


def _similar(a: str, b: str, limiar: float = 0.72) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio() >= limiar


def identificar_entidade_camadas(texto: str, tipo_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    from src.api.tmdb import identificar_entidade

    dados = _carregar()
    t = texto.strip()

    if tipo_hint in (None, "filme"):
        for f in dados.get("filmes", []):
            tit = f.get("titulo") or ""
            orig = f.get("titulo_original") or ""
            if _similar(t, tit) or (orig and _similar(t, orig)):
                print("[Knowledge] dataset_conhecimento.json (filme):", tit, "| consulta:", repr(t))
                return {
                    "tipo":    "filme",
                    "id":      f["id"],
                    "nome":    tit,
                    "ano":     f.get("ano") or None,
                    "generos": f.get("generos") or [],
                }

    if tipo_hint in (None, "ator"):
        for p in dados.get("pessoas", []):
            nome = p.get("nome") or ""
            if nome and _similar(t, nome, limiar=0.82):
                print("[Knowledge] dataset_conhecimento.json (ator):", nome, "| consulta:", repr(t))
                return {
                    "tipo":    "ator",
                    "id":      p["id"],
                    "nome":    nome,
                    "generos": [],
                }

    return identificar_entidade(texto, tipo_hint)
