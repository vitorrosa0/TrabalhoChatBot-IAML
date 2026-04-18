"""
Minera dados do TMDB para cache local (offline-first).
Gera ``data/dataset_conhecimento.json`` com filmes populares, pessoas em alta
e o léxico de países alinhado ao módulo ``src.nlp.paises``.

Uso (na raiz do projeto):
    python scripts/bootstrap_conhecimento.py
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.api.tmdb import GENERO_ID_PARA_CHAVE, _get  # noqa: E402
from src.nlp.paises import MAPA_PAISES, NOMES_PAISES  # noqa: E402

OUT_PATH = os.path.join(ROOT, "data", "dataset_conhecimento.json")
MAX_FILMES = 500
MAX_PESSOAS = 200


def _filme_resumo(item: dict) -> dict:
    gids = item.get("genre_ids") or []
    generos = [GENERO_ID_PARA_CHAVE[g] for g in gids if g in GENERO_ID_PARA_CHAVE]
    origens = item.get("origin_country") or []
    return {
        "id": item.get("id"),
        "titulo": item.get("title") or "",
        "titulo_original": item.get("original_title") or "",
        "generos": generos,
        "ano": (item.get("release_date") or "")[:4],
        "origem": origens,
    }


def minerar_filmes(limite: int) -> list:
    vistos: set[int] = set()
    saida: list = []
    pagina = 1
    while len(saida) < limite and pagina <= 25:
        dados = _get("/movie/popular", {"page": pagina})
        if not dados or not dados.get("results"):
            break
        for item in dados["results"]:
            fid = item.get("id")
            if fid in vistos:
                continue
            vistos.add(fid)
            saida.append(_filme_resumo(item))
            if len(saida) >= limite:
                break
        pagina += 1
        time.sleep(0.25)
    return saida


def minerar_pessoas(limite: int) -> list:
    vistos: set[int] = set()
    saida: list = []
    pagina = 1
    while len(saida) < limite and pagina <= 20:
        dados = _get("/trending/person/week", {"page": pagina})
        if not dados or not dados.get("results"):
            break
        for item in dados["results"]:
            pid = item.get("id")
            if pid in vistos:
                continue
            vistos.add(pid)
            saida.append({
                "id": pid,
                "nome": item.get("name") or "",
                "popularidade": item.get("popularity"),
                "departamento": item.get("known_for_department"),
            })
            if len(saida) >= limite:
                break
        pagina += 1
        time.sleep(0.25)
    return saida


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    payload = {
        "filmes": minerar_filmes(MAX_FILMES),
        "pessoas": minerar_pessoas(MAX_PESSOAS),
        "paises_lexico": {
            "codigo_para_termos": MAPA_PAISES,
            "codigo_para_rotulo": NOMES_PAISES,
        },
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Gravado: {OUT_PATH} ({len(payload['filmes'])} filmes, {len(payload['pessoas'])} pessoas)")


if __name__ == "__main__":
    main()
