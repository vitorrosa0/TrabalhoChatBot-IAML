import uuid

_sessoes = {}

CAMPOS_ORDEM = ["genero_pedido", "humor", "acompanhado", "duracao_preferida", "disposicao"]

TRIGGERS_RECOMENDACAO = {1, 4, 5}

PERGUNTAS = {
    "humor":             "Como você está se sentindo agora? (ex: animado, calmo, entediado, curioso, romântico, assustado)",
    "acompanhado":       "Vai assistir sozinho, com amigos, em casal ou com a família?",
    "duracao_preferida": "Prefere um filme curto (até 90min), médio (90–120min) ou longo (mais de 2h)?",
    "disposicao":        "Quer algo pra pensar e refletir, ou prefere desligar o cérebro e só curtir?",
}

def criar_sessao():
    sid = str(uuid.uuid4())
    _sessoes[sid] = {campo: None for campo in CAMPOS_ORDEM}
    _sessoes[sid]["filmes_recomendados"] = []
    _sessoes[sid]["generos_banidos"]     = []
    _sessoes[sid]["genero_travado"]      = False
    _sessoes[sid]["genero_recomendado"]  = None
    _sessoes[sid]["referencia"]          = None
    _sessoes[sid]["pais"]                = None
    return sid

def obter_sessao(sid):
    return _sessoes.get(sid)

def preencher_campo(sid, campo, valor):
    if sid in _sessoes and campo in _sessoes[sid]:
        _sessoes[sid][campo] = valor

def adicionar_filmes_recomendados(sid, titulos):
    if sid in _sessoes:
        _sessoes[sid]["filmes_recomendados"].extend(titulos)

def filmes_ja_recomendados(sid):
    return _sessoes.get(sid, {}).get("filmes_recomendados", [])

def campos_preenchidos(sid):
    sessao = _sessoes.get(sid, {})
    return [c for c in CAMPOS_ORDEM if sessao.get(c) is not None]

def proximo_campo_vazio(sid):
    sessao = _sessoes.get(sid, {})
    for campo in CAMPOS_ORDEM:
        if sessao.get(campo) is None:
            return campo
    return None

def sessao_completa(sid):
    return proximo_campo_vazio(sid) is None

def deve_recomendar(sid):
    return len(campos_preenchidos(sid)) in TRIGGERS_RECOMENDACAO

def encerrar_sessao(sid):
    return _sessoes.pop(sid, None)

def banir_genero(sid, genero):
    if sid in _sessoes and genero not in _sessoes[sid]["generos_banidos"]:
        _sessoes[sid]["generos_banidos"].append(genero)
        print(f"[Sessão] Gênero banido: {genero} | Banidos: {_sessoes[sid]['generos_banidos']}")

def generos_banidos(sid):
    return _sessoes.get(sid, {}).get("generos_banidos", [])

def travar_genero(sid):
    if sid in _sessoes:
        _sessoes[sid]["genero_travado"] = True
        print(f"[Sessão] Gênero travado para: {_sessoes[sid].get('genero_pedido')}")

def genero_esta_travado(sid):
    return _sessoes.get(sid, {}).get("genero_travado", False)

def destravar_genero(sid):
    if sid in _sessoes:
        _sessoes[sid]["genero_travado"] = False

def set_genero_recomendado(sid, genero):
    if sid in _sessoes:
        _sessoes[sid]["genero_recomendado"] = genero

def get_genero_recomendado(sid):
    return _sessoes.get(sid, {}).get("genero_recomendado")

def set_referencia(sid, tipo, id_, nome, generos=None, ano=None):
    if sid in _sessoes:
        ref = {"tipo": tipo, "id": id_, "nome": nome}
        if generos is not None:
            ref["generos"] = generos
        if ano:
            ref["ano"] = ano
        _sessoes[sid]["referencia"] = ref

def get_referencia(sid):
    return _sessoes.get(sid, {}).get("referencia")

def set_pais(sid, pais):
    if sid in _sessoes:
        _sessoes[sid]["pais"] = pais

def get_pais(sid):
    return _sessoes.get(sid, {}).get("pais")
