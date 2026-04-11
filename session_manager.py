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