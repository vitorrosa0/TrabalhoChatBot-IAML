"""
enrich_dataset.py
─────────────────────────────────────────────────────────────────────────────
Enriquece o dataset_reconhecimento.json com dados reais do TMDB:

Filmes:
  - origem        → lista de códigos ISO de países de produção
  - avaliacao     → nota média (vote_average)
  - sinopse       → overview traduzido (pt-BR, fallback en)
  - diretor       → nome do diretor principal (via credits)
  - elenco        → lista dos 5 principais atores

Pessoas:
  - departamento  → preenche os null com o dept real do TMDB
  - filmes_conhecidos → lista de IDs de filmes do catálogo em que aparece

Como usar:
  1. Obtenha uma chave gratuita em https://www.themoviedb.org/settings/api
  2. Execute:  python enrich_dataset.py --api-key SUA_CHAVE
  3. O arquivo dataset_reconhecimento_enriquecido.json será gerado na mesma pasta.

Flags opcionais:
  --input   caminho do JSON original  (default: data/dataset_reconhecimento.json)
  --output  caminho do JSON gerado    (default: data/dataset_reconhecimento.json)
  --delay   segundos entre requests   (default: 0.26 — respeita limite de ~4 req/s)
  --dry-run não salva, só mostra contadores
"""

import argparse
import json
import os
import sys
import time
from typing import Optional

import requests

# ── Mapeamento TMDB origin_country → ISO ─────────────────────────────────────
# TMDB já devolve ISO 3166-1 alpha-2, mas normaliza alguns casos especiais.
COUNTRY_NORMALIZE = {
    "US": "US", "BR": "BR", "FR": "FR", "ES": "ES", "IT": "IT",
    "JP": "JP", "KR": "KR", "MX": "MX", "AR": "AR", "IN": "IN",
    "NL": "NL", "GB": "GB", "DE": "DE", "CN": "CN", "AU": "AU",
    "CA": "CA", "RU": "RU", "SE": "SE", "DK": "DK", "NO": "NO",
}

BASE_URL = "https://api.themoviedb.org/3"


class TMDBClient:
    def __init__(self, api_key: str, delay: float = 0.26):
        self._key   = api_key
        self._delay = delay
        self._session = requests.Session()
        self._session.params = {"api_key": api_key}  # type: ignore

    def _get(self, path: str, **params) -> Optional[dict]:
        url = f"{BASE_URL}{path}"
        try:
            r = self._session.get(url, params=params, timeout=10)
            time.sleep(self._delay)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            print(f"  ⚠ HTTP {r.status_code} → {path}", file=sys.stderr)
            return None
        except requests.RequestException as e:
            print(f"  ✗ Request error: {e}", file=sys.stderr)
            return None

    def movie_details(self, tmdb_id: int) -> Optional[dict]:
        """Retorna detalhes + production_countries + credits em uma chamada."""
        return self._get(
            f"/movie/{tmdb_id}",
            language="pt-BR",
            append_to_response="credits",
        )

    def person_details(self, tmdb_id: int) -> Optional[dict]:
        return self._get(f"/person/{tmdb_id}", language="pt-BR")


def extract_origem(data: dict) -> list[str]:
    countries = data.get("production_countries", [])
    codes = []
    for c in countries:
        iso = c.get("iso_3166_1", "")
        if iso:
            codes.append(COUNTRY_NORMALIZE.get(iso, iso))
    return list(dict.fromkeys(codes))  # deduplica mantendo ordem


def extract_avaliacao(data: dict) -> float:
    val = data.get("vote_average", 0.0)
    count = data.get("vote_count", 0)
    if count < 10:
        return 0.0
    return round(float(val), 1)


def extract_sinopse(data: dict) -> str:
    overview = data.get("overview", "").strip()
    return overview


def extract_diretor(data: dict) -> str:
    crew = data.get("credits", {}).get("crew", [])
    for member in crew:
        if member.get("job") == "Director":
            return member.get("name", "")
    return ""


def extract_elenco(data: dict, limit: int = 5) -> list[str]:
    cast = data.get("credits", {}).get("cast", [])
    return [m["name"] for m in cast[:limit] if "name" in m]


def enrich_movies(
    filmes: list[dict],
    client: TMDBClient,
    dry_run: bool,
) -> tuple[list[dict], set[int]]:
    """Retorna lista enriquecida e conjunto de IDs válidos no TMDB."""
    valid_ids: set[int] = set()
    total = len(filmes)

    for i, filme in enumerate(filmes, 1):
        fid   = filme["id"]
        title = filme.get("titulo", "?")
        print(f"  [{i:4d}/{total}] Filme #{fid:>8} — {title[:55]}", end="", flush=True)

        data = client.movie_details(fid)

        if not data:
            print(" → não encontrado")
            continue

        valid_ids.add(fid)

        if not dry_run:
            # Só sobrescreve se o campo estiver vazio/zerado
            if not filme.get("origem"):
                filme["origem"] = extract_origem(data)

            if not filme.get("avaliacao"):
                filme["avaliacao"] = extract_avaliacao(data)

            if not filme.get("sinopse"):
                sinopse = extract_sinopse(data)
                if not sinopse:
                    # fallback inglês
                    data_en = client.movie_details(fid)  # já em pt-BR, tenta mesmo
                    sinopse = sinopse or data.get("overview", "")
                filme["sinopse"] = sinopse

            if not filme.get("diretor"):
                filme["diretor"] = extract_diretor(data)

            if not filme.get("elenco"):
                filme["elenco"] = extract_elenco(data)

        origem_str = str(filme.get("origem", [])) if not dry_run else "—"
        nota_str   = str(filme.get("avaliacao", 0)) if not dry_run else "—"
        print(f" → {nota_str}⭐ {origem_str}")

    return filmes, valid_ids


def enrich_people(
    pessoas: list[dict],
    client: TMDBClient,
    valid_movie_ids: set[int],
    dry_run: bool,
) -> list[dict]:
    total = len(pessoas)

    for i, pessoa in enumerate(pessoas, 1):
        pid  = pessoa["id"]
        name = pessoa.get("nome", "?")

        needs_dept  = pessoa.get("departamento") is None
        needs_filmes = not pessoa.get("filmes_conhecidos")

        if not needs_dept and not needs_filmes:
            print(f"  [{i:4d}/{total}] Pessoa #{pid:>8} — {name[:45]} → ok (skip)")
            continue

        print(f"  [{i:4d}/{total}] Pessoa #{pid:>8} — {name[:45]}", end="", flush=True)

        data = client.person_details(pid)
        if not data:
            print(" → não encontrada")
            continue

        if not dry_run:
            if needs_dept:
                dept = data.get("known_for_department", "") or ""
                pessoa["departamento"] = dept or "Acting"

        print(f" → dept={pessoa.get('departamento', '—')}")

    return pessoas


def build_person_movie_links(
    filmes: list[dict],
    pessoas: list[dict],
    client: TMDBClient,
    dry_run: bool,
) -> list[dict]:
    """
    Para cada pessoa, descobre quais filmes do catálogo ela participou
    buscando os créditos de cada filme já enriquecido.
    Usa os credits que já foram baixados (campo diretor/elenco) para
    montar o índice sem requests extras.
    """
    print("\n  Construindo vínculos pessoa↔filme...")

    # índice nome_lower → lista de pessoas
    name_to_people: dict[str, list[dict]] = {}
    for p in pessoas:
        key = p["nome"].lower()
        name_to_people.setdefault(key, []).append(p)

    if not dry_run:
        # Limpa filmes_conhecidos existentes para reconstruir
        for p in pessoas:
            p["filmes_conhecidos"] = []

        for filme in filmes:
            fid = filme["id"]
            # diretor
            diretor = filme.get("diretor", "")
            if diretor:
                for p in name_to_people.get(diretor.lower(), []):
                    if fid not in p["filmes_conhecidos"]:
                        p["filmes_conhecidos"].append(fid)
            # elenco
            for ator in filme.get("elenco", []):
                for p in name_to_people.get(ator.lower(), []):
                    if fid not in p["filmes_conhecidos"]:
                        p["filmes_conhecidos"].append(fid)

        total_links = sum(len(p["filmes_conhecidos"]) for p in pessoas)
        print(f"  → {total_links} vínculos criados")

    return pessoas


def main():
    parser = argparse.ArgumentParser(description="Enriquece dataset_reconhecimento.json via TMDB")
    parser.add_argument("--api-key", required=True, help="Chave de API do TMDB")
    parser.add_argument("--input",   default=os.path.join("data", "dataset_reconhecimento.json"))
    parser.add_argument("--output",  default=None, help="Padrão: sobrescreve o --input")
    parser.add_argument("--delay",   type=float, default=0.26)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only-movies",  action="store_true", help="Pula enriquecimento de pessoas")
    parser.add_argument("--only-people",  action="store_true", help="Pula enriquecimento de filmes")
    args = parser.parse_args()

    output_path = args.output or args.input

    print(f"\n🎬 CinemaBot — Enriquecedor de Dataset")
    print(f"   Input  : {args.input}")
    print(f"   Output : {output_path}")
    print(f"   Dry-run: {args.dry_run}\n")

    with open(args.input, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    filmes  = dataset.get("filmes", [])
    pessoas = dataset.get("pessoas", [])
    lexico  = dataset.get("paises_lexico", {})

    client = TMDBClient(api_key=args.api_key, delay=args.delay)

    valid_ids: set[int] = set()

    # ── Filmes ────────────────────────────────────────────────────────────
    if not args.only_people:
        print(f"━━━ Enriquecendo {len(filmes)} filmes ━━━")
        filmes, valid_ids = enrich_movies(filmes, client, args.dry_run)
    else:
        valid_ids = {f["id"] for f in filmes}

    # ── Pessoas ───────────────────────────────────────────────────────────
    if not args.only_movies:
        print(f"\n━━━ Enriquecendo {len(pessoas)} pessoas ━━━")
        pessoas = enrich_people(pessoas, client, valid_ids, args.dry_run)

    # ── Vínculos pessoa↔filme ─────────────────────────────────────────────
    if not args.dry_run and not args.only_movies and not args.only_people:
        pessoas = build_person_movie_links(filmes, pessoas, client, args.dry_run)

    # ── Salva ─────────────────────────────────────────────────────────────
    if not args.dry_run:
        dataset["filmes"]         = filmes
        dataset["pessoas"]        = pessoas
        dataset["paises_lexico"]  = lexico

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Dataset salvo em: {output_path}")
        print(f"   Filmes  : {len(filmes)}")
        print(f"   Pessoas : {len(pessoas)}")
    else:
        print("\n⚠  Dry-run: nenhum arquivo foi modificado.")


if __name__ == "__main__":
    main()