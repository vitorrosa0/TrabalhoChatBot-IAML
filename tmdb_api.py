import requests

TMDB_API_KEY = "334e50050d16da0c941e5006fee5e7e8"
TMDB_BASE_URL = "https://api.themoviedb.org/3"


def _get(endpoint, params={}):
    params["api_key"] = TMDB_API_KEY
    params["language"] = "pt-BR"
    try:
        response = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def buscar_nota_filme(titulo):
    dados = _get("/search/movie", {"query": titulo})

    if not dados or not dados.get("results"):
        return None

    filme = dados["results"][0]
    nota = filme.get("vote_average")

    if not nota:
        return None

    return round(nota, 1)