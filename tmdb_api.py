import requests

TMDB_API_KEY = "334e50050d16da0c941e5006fee5e7e8"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

GENEROS_TMDB = {
    "acao":              28,
    "comedia":           35,
    "drama":             18,
    "terror":            27,
    "romance":           10749,
    "ficcao_cientifica": 878,
    "animacao":          16,
    "suspense":          53,
}

DURACAO_FILTROS = {
    "curto": {"with_runtime.lte": 90},
    "medio": {"with_runtime.gte": 90, "with_runtime.lte": 120},
    "longo": {"with_runtime.gte": 120},
}


def _get(endpoint, params={}):
    params = dict(params)
    params["api_key"] = TMDB_API_KEY
    params["language"] = "pt-BR"
    try:
        response = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def _buscar_duracao(filme_id):
    dados = _get(f"/movie/{filme_id}")
    if not dados:
        return None
    runtime = dados.get("runtime")
    return runtime if runtime and runtime > 0 else None


def buscar_filmes_por_genero(genero, quantidade=3, excluir_titulos=None, duracao=None):
    excluir_titulos = set(excluir_titulos or [])
    genero_id = GENEROS_TMDB.get(genero)
    if not genero_id:
        return []

    params_base = {
        "with_genres":    genero_id,
        "sort_by":        "vote_average.desc",
        "vote_count.gte": 500,
    }

    if duracao and duracao in DURACAO_FILTROS:
        params_base.update(DURACAO_FILTROS[duracao])
        print(f"[TMDB] Filtro de duração '{duracao}': {DURACAO_FILTROS[duracao]}")

    filmes  = []
    pagina  = 1

    while len(filmes) < quantidade and pagina <= 5:
        dados = _get("/discover/movie", {**params_base, "page": pagina})

        if not dados or not dados.get("results"):
            break

        print(f"[TMDB] Página {pagina} — {len(dados['results'])} resultados brutos")

        for filme in dados["results"]:
            titulo = filme.get("title", "Sem título")
            nota   = round(filme.get("vote_average", 0), 1)
            ano    = filme.get("release_date", "????")[:4]
            print(f"  {'✗ (já recomendado)' if titulo in excluir_titulos else '✓'} {titulo} ({ano}) ⭐ {nota}")

            if titulo in excluir_titulos:
                continue

            filme_id      = filme.get("id")
            duracao_min   = _buscar_duracao(filme_id) if filme_id else None
            print(f"  [TMDB] Duração de '{titulo}': {duracao_min} min")

            filmes.append({
                "titulo":      titulo,
                "ano":         ano,
                "descricao":   filme.get("overview", "Sem descrição disponível."),
                "nota":        nota,
                "duracao_min": duracao_min,
            })

            if len(filmes) >= quantidade:
                break

        pagina += 1

    print(f"[TMDB] Retornando {len(filmes)} filmes para gênero '{genero}' duração '{duracao}'")
    return filmes


def buscar_nota_filme(titulo):
    dados = _get("/search/movie", {"query": titulo})
    if not dados or not dados.get("results"):
        return None
    nota = dados["results"][0].get("vote_average")
    return round(nota, 1) if nota else None