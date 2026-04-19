import re
import time
import requests
from difflib import SequenceMatcher

TMDB_API_KEY = "334e50050d16da0c941e5006fee5e7e8"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

GENEROS_TMDB = {
    "acao":              28,
    "aventura":          12,
    "animacao":          16,
    "cinema_tv":         10770,
    "comedia":           35,
    "crime":             80,
    "documentario":      99,
    "drama":             18,
    "familia":           10751,
    "fantasia":          14,
    "faroeste":          37,
    "ficcao_cientifica": 878,
    "guerra":            10752,
    "historia":          36,
    "misterio":          9648,
    "musica":            10402,
    "romance":           10749,
    "suspense":          53,
    "terror":            27,
}

DURACAO_FILTROS = {
    "curto": {"with_runtime.lte": 90},
    "medio": {"with_runtime.gte": 90, "with_runtime.lte": 120},
    "longo": {"with_runtime.gte": 120},
}

MAPA_KEYWORDS = {
    # 4.1 - Ficção e Futuro
    "espaco": ["space", "outer space", "galaxy", "planet", "spaceship", "stars"],
    "tecnologia": ["technology", "high tech", "hacker", "internet", "computer", "virtual reality"],
    "viagem_no_tempo": ["time travel", "time loop", "time machine", "changing the past"],
    "inteligencia_artificial": ["artificial intelligence", "ai", "machine learning", "cyborg", "android", "computer program"],
    "distopia": ["dystopia", "dystopian", "totalitarianism", "oppression", "new world order"],
    "pos_apocalitico": ["post-apocalyptic", "apocalypse", "end of the world", "ruins", "wasteland", "post-apocalyptic future"],
    "cyberpunk": ["cyberpunk", "hacker", "netrunner", "mega corporation"],
    "aliens": ["alien", "extraterrestrial", "alien invasion", "ufo", "alien planet", "martian"],
    "futuro": ["future", "futurism", "futuristic", "22nd century", "21st century"],
    "robos": ["robot", "robotics", "mecha", "automaton", "cyborg", "android"],

    # 4.2 - Conflito e Crime
    "batalha": ["battle", "epic battle", "combat", "fight", "warfare"],
    "guerra": ["war", "world war", "civil war", "soldier", "military"],
    "crime": ["crime", "criminal", "murder", "robbery", "heist", "underworld"],
    "investigacao": ["investigation", "detective", "police investigation", "clue", "whodunit", "mystery"],
    "espionagem": ["espionage", "spy", "secret agent", "cia", "kgb", "mi6", "undercover"],
    "vinganca": ["revenge", "vengeance", "avenger", "vendetta", "payback"],
    "assalto": ["heist", "bank robbery", "thief", "steal", "burglary", "robbery"],
    "prisao": ["prison", "jail", "prisoner", "prison escape", "behind bars"],
    "serial_killer": ["serial killer", "psychopath", "mass murderer", "sociopath", "killer"],
    "gangsters": ["gangster", "mafia", "mobster", "yakuza", "triad", "gang"],
    "tribunal": ["court", "courtroom", "trial", "lawyer", "judge", "legal"],
    "mafia": ["mafia", "organized crime", "mob", "cosa nostra", "cartel"],

    # 4.3 - Fantasia e Medo
    "magia": ["magic", "wizard", "spell", "witchcraft", "sorcery"],
    "sobrenatural": ["supernatural", "paranormal", "occult", "spirit", "curse"],
    "vampiros": ["vampire", "dracula", "bloodsucker", "vampirism", "undead", "vampires"],
    "zumbis": ["zombie", "living dead", "zombie apocalypse", "infected", "undead", "zombies"],
    "monstros": ["monster", "creature", "kaiju", "beast", "giant monster"],
    "fantasmas": ["ghost", "haunted house", "spirit", "poltergeist", "apparition", "ghosts"],
    "mitologia": ["mythology", "greek mythology", "norse mythology", "gods", "myth"],
    "bruxas": ["witch", "witchcraft", "coven", "witches", "sorceress"],
    "demonios": ["demon", "devil", "hell", "possession", "exorcism", "demons"],
    "slasher": ["slasher", "teen slasher", "gore", "body count", "slasher movie"],
    "terror_psicologico": ["psychological thriller", "paranoia", "hallucination", "madness", "mind game", "psychological horror"],

    # 4.4 - Ação e Estilo
    "super_heroi": ["superhero", "marvel", "dc comics", "mutant", "comic book"],
    "artes_marciais": ["martial arts", "kung fu", "karate", "ninja", "taekwondo", "martial artist"],
    "carros": ["car", "car race", "car chase", "street racing", "auto racing", "cars"],
    "samurai": ["samurai", "ronin", "feudal japan", "katana", "sword fight"],
    "faroeste": ["western", "cowboy", "wild west", "spaghetti western", "outlaw"],
    "noir": ["noir", "film noir", "detective", "femme fatale", "cynicism"],
    "neo_noir": ["neo-noir", "modern noir", "hardboiled", "urban decay"],
    "sobrevivencia": ["survival", "stranded", "wilderness", "survival horror", "marooned"],
    "esportes": ["sports", "athlete", "competition", "tournament", "coach", "sport"],

    # 4.5 - Temas e Vida
    "baseado_em_fatos": ["based on true story", "true story", "based on real events", "historical event", "real life", "based on a true story"],
    "biografico": ["biography", "biopic", "life story", "historical figure"],
    "musical": ["musical", "singing", "dance", "broadway", "music"],
    "comedia_romantica": ["romantic comedy", "rom-com", "love", "meet cute", "romance"],
    "satira": ["satire", "dark comedy", "parody", "mockumentary", "irony"],
    "drama_familiar": ["family drama", "dysfunctional family", "parent child relationship", "family conflict", "domestic"],
    "natureza": ["nature", "wilderness", "forest", "jungle", "ocean", "wildlife"],
    "animais": ["animal", "dog", "wild animal", "pet", "creature", "animals"],
    "politica": ["politics", "political", "president", "election", "government"],
    "coming_of_age": ["coming of age", "teenager", "high school", "growing up", "youth"]
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


_TMDB_LOGO_BASE = "https://image.tmdb.org/t/p/w45"

def _buscar_plataformas(filme_id, pais="BR"):
    dados = _get(f"/movie/{filme_id}/watch/providers")
    if not dados:
        return []
    resultado = dados.get("results", {}).get(pais, {})
    flatrate = resultado.get("flatrate", [])
    return [
        {"nome": p["provider_name"], "logo": f"{_TMDB_LOGO_BASE}{p['logo_path']}"}
        for p in flatrate if p.get("logo_path")
    ]


def buscar_filmes_por_genero(genero, quantidade=3, excluir_titulos=None, duracao=None, pais=None):
    excluir_titulos = set(excluir_titulos or [])
    genero_id = GENEROS_TMDB.get(genero) if genero else None
    if not genero_id and not pais:
        return []

    params_base = {
        "sort_by":        "vote_average.desc",
        "vote_count.gte": 200 if pais else 500,
    }

    if genero_id:
        params_base["with_genres"] = genero_id

    if pais:
        params_base["with_origin_country"] = pais
        print(f"[TMDB] Filtro de país: '{pais}'")

    if duracao and duracao in DURACAO_FILTROS:
        params_base.update(DURACAO_FILTROS[duracao])
        print(f"[TMDB] Filtro de duração '{duracao}': {DURACAO_FILTROS[duracao]}")

    filmes = []
    pagina = 1

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

            filme_id    = filme.get("id")
            duracao_min = _buscar_duracao(filme_id) if filme_id else None
            plataformas = _buscar_plataformas(filme_id) if filme_id else []
            print(f"  [TMDB] Duração de '{titulo}': {duracao_min} min")

            filmes.append({
                "titulo":      titulo,
                "ano":         ano,
                "descricao":   filme.get("overview", "Sem descrição disponível."),
                "nota":        nota,
                "duracao_min": duracao_min,
                "plataformas": plataformas,
            })

            if len(filmes) >= quantidade:
                break

        pagina += 1

    print(f"[TMDB] Retornando {len(filmes)} filmes para gênero '{genero}' duração '{duracao}' país '{pais}'")
    return filmes


def buscar_nota_filme(titulo):
    dados = _get("/search/movie", {"query": titulo})
    if not dados or not dados.get("results"):
        return None
    nota = dados["results"][0].get("vote_average")
    return round(nota, 1) if nota else None


GENERO_ID_PARA_CHAVE = {v: k for k, v in GENEROS_TMDB.items()}

_STOPWORDS_TITULO = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos",
                     "das", "e", "em", "no", "na", "the", "of", "and", "in"}


def _match_titulo(texto, titulo, titulo_original=""):
    t = texto.lower().strip()
    sim1 = SequenceMatcher(None, t, titulo.lower()).ratio()
    sim2 = SequenceMatcher(None, t, titulo_original.lower()).ratio() if titulo_original else 0
    if max(sim1, sim2) >= 0.4:
        return True
    palavras       = set(re.sub(r"[^\w\s]", "", t).split()) - _STOPWORDS_TITULO
    palavras_titulo = set(re.sub(r"[^\w\s]", "", titulo.lower()).split())
    palavras_orig   = set(re.sub(r"[^\w\s]", "", titulo_original.lower()).split())
    return bool(palavras) and bool(palavras & (palavras_titulo | palavras_orig))


def _match_pessoa(texto, nome):
    palavras = [p for p in texto.lower().split() if len(p) > 2]
    return any(p in nome.lower() for p in palavras)


def identificar_entidade(texto, tipo_hint=None):
    texto = texto.strip()

    if tipo_hint in (None, "filme"):
        dados = _get("/search/movie", {"query": texto})
        if dados and dados.get("results"):
            melhor      = dados["results"][0]
            titulo      = melhor.get("title", "")
            titulo_orig = melhor.get("original_title", "")
            if _match_titulo(texto, titulo, titulo_orig):
                genero_ids = melhor.get("genre_ids", [])
                generos = [GENERO_ID_PARA_CHAVE[g] for g in genero_ids
                           if g in GENERO_ID_PARA_CHAVE]
                return {
                    "tipo":    "filme",
                    "id":      melhor["id"],
                    "nome":    titulo,
                    "ano":     melhor.get("release_date", "")[:4],
                    "generos": generos,
                }

    if tipo_hint in (None, "ator"):
        dados = _get("/search/person", {"query": texto})
        if dados and dados.get("results"):
            melhor = dados["results"][0]
            if melhor.get("popularity", 0) >= 1 and _match_pessoa(texto, melhor["name"]):
                return {
                    "tipo":    "ator",
                    "id":      melhor["id"],
                    "nome":    melhor["name"],
                    "generos": [],
                }

    return None


def buscar_filmes_similares(filme_id, generos_filme=None, quantidade=3, excluir_titulos=None):
    excluir_titulos = set(excluir_titulos or [])
    filmes = []

    for endpoint in [f"/movie/{filme_id}/recommendations", f"/movie/{filme_id}/similar"]:
        if len(filmes) >= quantidade:
            break
        dados = _get(endpoint)
        if not dados or not dados.get("results"):
            continue
        for filme in dados["results"]:
            titulo = filme.get("title", "Sem título")
            if titulo in excluir_titulos:
                continue
            nota = round(filme.get("vote_average", 0), 1)
            if nota < 5.0 or filme.get("vote_count", 0) < 50:
                continue
            ano = (filme.get("release_date") or "????")[:4]
            fid = filme.get("id")
            duracao_min = _buscar_duracao(fid) if fid else None
            plataformas = _buscar_plataformas(fid) if fid else []
            filmes.append({
                "titulo":      titulo,
                "ano":         ano,
                "descricao":   filme.get("overview") or "Sem descrição disponível.",
                "nota":        nota,
                "duracao_min": duracao_min,
                "plataformas": plataformas,
            })
            if len(filmes) >= quantidade:
                break

    if not filmes and generos_filme:
        for genero in generos_filme:
            candidatos = buscar_filmes_por_genero(genero, quantidade=quantidade,
                                                  excluir_titulos=excluir_titulos)
            if candidatos:
                return candidatos

    return filmes


def buscar_filmes_por_ator(pessoa_id, quantidade=3, excluir_titulos=None):
    excluir_titulos = set(excluir_titulos or [])
    dados = _get("/discover/movie", {
        "with_people":    pessoa_id,
        "sort_by":        "vote_average.desc",
        "vote_count.gte": 200,
    })
    if not dados or not dados.get("results"):
        return []

    filmes = []
    for filme in dados["results"]:
        titulo = filme.get("title", "Sem título")
        if titulo in excluir_titulos:
            continue
        nota = round(filme.get("vote_average", 0), 1)
        ano  = (filme.get("release_date") or "????")[:4]
        fid  = filme.get("id")
        duracao_min = _buscar_duracao(fid) if fid else None
        plataformas = _buscar_plataformas(fid) if fid else []
        filmes.append({
            "titulo":      titulo,
            "ano":         ano,
            "descricao":   filme.get("overview") or "Sem descrição disponível.",
            "nota":        nota,
            "duracao_min": duracao_min,
            "plataformas": plataformas,
        })
        if len(filmes) >= quantidade:
            break
    return filmes


_TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"
_cache_destaques: dict = {"data": None, "ts": 0.0}
_CACHE_TTL = 1800


def buscar_destaques(quantidade=8):
    global _cache_destaques
    agora = time.time()
    if _cache_destaques["data"] is not None and agora - _cache_destaques["ts"] < _CACHE_TTL:
        return _cache_destaques["data"]

    dados = _get("/movie/popular", {"page": 1})
    if not dados or not dados.get("results"):
        return _cache_destaques["data"] or []

    filmes = []
    for filme in dados["results"]:
        poster = filme.get("poster_path")
        if not poster:
            continue
        nota = round(filme.get("vote_average", 0), 1)
        if nota < 6.5 or filme.get("vote_count", 0) < 300:
            continue
        titulo = filme.get("title", "")
        ano    = (filme.get("release_date") or "")[:4]
        fid    = filme.get("id")
        duracao_min = _buscar_duracao(fid) if fid else None
        filmes.append({
            "id":          fid,
            "titulo":      titulo,
            "ano":         ano,
            "nota":        nota,
            "duracao_min": duracao_min,
            "poster_url":  f"{_TMDB_IMG_BASE}{poster}",
        })
        if len(filmes) >= quantidade:
            break

    _cache_destaques = {"data": filmes, "ts": agora}
    return filmes


def buscar_filmes_por_genero_e_ator(genero, pessoa_id, quantidade=3, excluir_titulos=None):
    excluir_titulos = set(excluir_titulos or [])
    genero_id = GENEROS_TMDB.get(genero)
    if not genero_id:
        return []

    dados = _get("/discover/movie", {
        "with_genres":    genero_id,
        "with_people":    pessoa_id,
        "sort_by":        "vote_average.desc",
        "vote_count.gte": 100,
    })
    if not dados or not dados.get("results"):
        return []

    filmes = []
    for filme in dados["results"]:
        titulo = filme.get("title", "Sem título")
        if titulo in excluir_titulos:
            continue
        nota = round(filme.get("vote_average", 0), 1)
        ano  = (filme.get("release_date") or "????")[:4]
        fid  = filme.get("id")
        duracao_min = _buscar_duracao(fid) if fid else None
        plataformas = _buscar_plataformas(fid) if fid else []
        filmes.append({
            "titulo":      titulo,
            "ano":         ano,
            "descricao":   filme.get("overview") or "Sem descrição disponível.",
            "nota":        nota,
            "duracao_min": duracao_min,
            "plataformas": plataformas,
        })
        if len(filmes) >= quantidade:
            break
    return filmes


def buscar_keywords_filme(filme_id):
    """
    Busca as keywords de um filme específico pelo seu ID no TMDB.
    """
    dados = _get(f"/movie/{filme_id}/keywords")
    if not dados or not dados.get("keywords"):
        return []
        
    keywords_ingles = []
    for k in dados.get("keywords", []):
        nome = k.get("name")
        if nome:
            keywords_ingles.append(nome.lower().strip())
            
    return keywords_ingles


def normalizar_keywords(lista_keywords_ingles):
    """
    Constrói um dicionário para mapear as inúmeras keywords brutas (em inglês)
    do TMDB para um léxico interno, com 50 tags base (em português).
    Retorna apenas as tags que existirem e sem duplicatas.
    """
    tags_encontradas = set()
    for kw in lista_keywords_ingles:
        kw_clean = kw.lower().strip()
        for tag, keywords_mapeadas in MAPA_KEYWORDS.items():
            if kw_clean in keywords_mapeadas:
                tags_encontradas.add(tag)
                
    return list(tags_encontradas)
