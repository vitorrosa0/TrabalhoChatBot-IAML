from typing import Optional, Dict, Any
from src.actions.base import BotAction
from src.actions.formatters import formatar_lista_filmes
from src.nlp.generos import NOMES_GENEROS
from src.nlp.paises import NOMES_PAISES
from src.api.tmdb import (
    buscar_filmes_por_genero, buscar_filmes_similares,
    buscar_filmes_por_ator, buscar_filmes_por_genero_e_ator,
)
from src.data.ml_recomendador import recomendar_com_ambos, salvar_exemplo
from src.core.session_manager import (
    obter_sessao, criar_sessao, encerrar_sessao, preencher_campo,
    deve_recomendar, proximo_campo_vazio, sessao_completa,
    adicionar_filmes_recomendados, filmes_ja_recomendados, PERGUNTAS,
    generos_banidos, travar_genero, genero_esta_travado,
    set_genero_recomendado, set_referencia, get_referencia, set_pais, get_pais,
    obter_tags_dominantes
)


def _ajustar_genero_com_semente_e_humor(genero_ml: str, humor: str, ref: Optional[Dict[str, Any]]) -> str:
    if not ref or ref.get("tipo") != "filme":
        return genero_ml
        
    genes = set(ref.get("generos") or [])
    
    # Fluxo Híbrido Avançado: Semente vs Humor
    pesados = {"acao", "terror", "guerra", "crime", "suspense"}
    leves   = {"comedia", "animacao", "familia", "romance", "aventura"}
    
    if humor in ["triste", "assustado"] and (genes & pesados):
        # Usuário quer um filme tipo Batman, mas está triste. ML alivia o peso.
        suavizador = {"acao": "aventura", "terror": "suspense", "guerra": "drama", "crime": "misterio", "suspense": "misterio"}
        return suavizador.get(genero_ml, genero_ml)
        
    if humor in ["animado", "entediado"] and (genes & leves):
        # Usuário quer um filme leve, mas tá com energia pra gastar (entediado). ML impulsiona pra ação/comédia.
        impulsionador = {"familia": "aventura", "romance": "comedia", "animacao": "fantasia"}
        return impulsionador.get(genero_ml, genero_ml)
        
    return genero_ml


def _resolver_genero_e_nota(genero_pedido, genero_j48, genero_lmt, banidos, travado):
    if travado and genero_pedido:
        return f"🤖 _Usando **{NOMES_GENEROS.get(genero_pedido, genero_pedido)}** conforme você pediu._\n\n", genero_pedido

    nome_pedido = f"**{NOMES_GENEROS.get(genero_pedido, genero_pedido)}**" if genero_pedido else "suas preferências"

    if genero_j48 is None:
        return f"🤖 _Ainda aprendendo... usando {nome_pedido}._\n\n", genero_pedido

    notas = {
        genero_lmt: (f"🤖 _J48 e LMT concordaram: **{NOMES_GENEROS.get(genero_j48, '')}** é o melhor para o seu perfil agora._\n\n", genero_j48),
    }
    nota_ml, genero_final = notas.get(genero_j48, (
        f"🤖 _J48 indicou **{NOMES_GENEROS.get(genero_j48, '')}** e LMT indicou **{NOMES_GENEROS.get(genero_lmt, '')}**. Usando J48._\n\n",
        genero_j48,
    ))

    if genero_final in banidos:
        return f"🤖 _O ML sugeriu um gênero que você não quer. Usando {nome_pedido} no lugar._\n\n", genero_pedido

    return nota_ml, genero_final


def _montar_resposta_filmes(sid):
    sessao        = obter_sessao(sid)
    pais          = get_pais(sid)
    genero_pedido = sessao.get("genero_pedido")

    if pais and not genero_pedido:
        ja_vistos = filmes_ja_recomendados(sid)
        filmes    = buscar_filmes_por_genero(None, quantidade=3, excluir_titulos=ja_vistos,
                                             duracao=sessao.get("duracao_preferida"), pais=pais)
        if not filmes:
            return "Hmm, não encontrei filmes para esse país no momento. 😅 Tente pedir um gênero também!"
        adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])
        nome_pais = NOMES_PAISES.get(pais, pais)
        return f"🎬 Aqui estão filmes {nome_pais} para você:\n\n" + formatar_lista_filmes(filmes) + "Se quiser mais ou um gênero específico, é só pedir! 😊"

    humor       = sessao.get("humor") or "calmo"
    acompanhado = sessao.get("acompanhado") or "sozinho"
    duracao     = sessao.get("duracao_preferida") or "medio"
    disposicao  = sessao.get("disposicao") or "curtir"
    banidos     = generos_banidos(sid)

    tags_usuario = obter_tags_dominantes(sid)
    genero_j48, genero_lmt = recomendar_com_ambos(genero_pedido, humor, acompanhado, duracao, disposicao, tags_usuario=tags_usuario)

    nota_ml, genero_final = _resolver_genero_e_nota(
        genero_pedido, genero_j48, genero_lmt, banidos, genero_esta_travado(sid)
    )
    ref = sessao.get("referencia")
    genero_final = _ajustar_genero_com_semente_e_humor(genero_final, humor, ref)

    ja_vistos = filmes_ja_recomendados(sid)
    set_genero_recomendado(sid, genero_final)
    filmes    = buscar_filmes_por_genero(genero_final, quantidade=3, excluir_titulos=ja_vistos,
                                         duracao=sessao.get("duracao_preferida"), pais=pais)
    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])

    nome_genero = NOMES_GENEROS.get(genero_final, genero_final) if genero_final else None
    nome_pais   = NOMES_PAISES.get(pais) if pais else None

    txt_pais = f" {nome_pais}" if nome_pais else ""
    txt_genero = f" de **{nome_genero}**" if nome_genero else ""

    cabecalho = f"🎬 Aqui estão os filmes{txt_pais}{txt_genero} pra você:\n\n"

    resposta = cabecalho + nota_ml + formatar_lista_filmes(filmes)

    if sessao_completa(sid):
        salvar_exemplo(genero_pedido, humor, acompanhado, duracao, disposicao, genero_final, tags_usuario=tags_usuario)
        encerrar_sessao(sid)
        return resposta + "Espero que curta! 🍿 Se quiser mais recomendações, é só pedir."

    proximo = proximo_campo_vazio(sid)
    return resposta + f"\n💬 {PERGUNTAS[proximo]}"


def _montar_resposta_por_entidade(sid):
    sessao    = obter_sessao(sid)
    ref       = get_referencia(sid)
    genero    = sessao.get("genero_pedido")
    ja_vistos = filmes_ja_recomendados(sid)

    if ref["tipo"] == "filme":
        filmes  = buscar_filmes_similares(ref["id"], generos_filme=ref.get("generos", []),
                                          quantidade=3, excluir_titulos=ja_vistos)
        ano_str = f" ({ref['ano']})" if ref.get("ano") else ""
        intro   = f"🎬 Baseado em **{ref['nome']}{ano_str}**, aqui estão filmes que você pode gostar:\n\n"
    elif ref["tipo"] == "ator" and genero:
        nome_genero = NOMES_GENEROS.get(genero, genero)
        filmes = buscar_filmes_por_genero_e_ator(genero, ref["id"], quantidade=3, excluir_titulos=ja_vistos)
        intro  = (
            f"🎬 Filmes de **{nome_genero}** com **{ref['nome']}**:\n\n" if filmes
            else f"🎬 Não encontrei {nome_genero} com **{ref['nome']}**. Mas separei outros dele(a):\n\n"
        )
        filmes = filmes or buscar_filmes_por_ator(ref["id"], quantidade=3, excluir_titulos=ja_vistos)
    else:
        filmes = buscar_filmes_por_ator(ref["id"], quantidade=3, excluir_titulos=ja_vistos)
        intro  = f"🎬 Aqui estão filmes com **{ref['nome']}**:\n\n"

    if not filmes:
        return f"Hmm, não encontrei filmes para **{ref['nome']}** no momento. 😅\nTente outro nome ou um gênero!"

    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])
    return intro + formatar_lista_filmes(filmes) + "Se quiser mais, é só pedir! 😊"


class MaisFilmesAction(BotAction):
    def execute(self, contexto, sid):
        if not sid:
            return "Não temos uma conversa ativa. Me diz um gênero pra começar! 🎬", sid
        montar = _montar_resposta_por_entidade if get_referencia(sid) else _montar_resposta_filmes
        return montar(sid), sid


class SuggestMovieAction(BotAction):
    def __init__(self, sessao_fns, entidade_fns, montar_fns, deteccao_fns):
        # Preservado para retrocompatibilidade do __init__ caso seja passado, mas usará import direto
        self._identificar_entidade = entidade_fns["identificar"]
        self._detectar_ator        = entidade_fns["detectar_ator"]
        self._tem_enfase      = deteccao_fns["tem_enfase"]

    def execute(self, contexto, sid):
        genero = contexto.get("genero_afirmado")
        mensagem = contexto["mensagem"]
        tipo_ref = contexto.get("tipo_ref")
        nome_ref = contexto.get("nome_ref")
        pais = contexto.get("pais")

        sessao = obter_sessao(sid) if sid else None
        genero_atual = sessao.get("genero_pedido") if sessao else None

        if sid and genero == genero_atual:
            if self._tem_enfase(mensagem, genero):
                travar_genero(sid)
                return (
                    f"Entendido! Vou te recomendar apenas **{NOMES_GENEROS[genero]}** daqui pra frente. 🎬\n\n"
                    + _montar_resposta_filmes(sid)
                ), sid
            return _montar_resposta_filmes(sid), sid

        if sid and genero and genero != genero_atual:
            encerrar_sessao(sid)
            sid = None

        if not sid and genero:
            sid = criar_sessao()
            preencher_campo(sid, "genero_pedido", genero)
            if pais:
                set_pais(sid, pais)

        # Trata semente de filme e ator (Extração de Contexto / Slot Filling Dinâmico)
        candidato = nome_ref if (tipo_ref in ["ator", "filme"]) else self._detectar_ator(mensagem)
        if candidato and sid:
            entidade = self._identificar_entidade(candidato, tipo_hint=tipo_ref or "ator")
            if entidade:
                set_referencia(
                    sid, entidade["tipo"], entidade["id"], entidade["nome"],
                    generos=entidade.get("generos"), ano=entidade.get("ano"),
                )
                
                # Slot Filling Dinâmico: Se a entidade for filme e tiver gêneros mapeados, preenchemos a sessão
                if entidade["tipo"] == "filme" and entidade.get("generos"):
                    genes = entidade["generos"]
                    if not obter_sessao(sid).get("genero_pedido"):
                        preencher_campo(sid, "genero_pedido", genes[0])
                        
                return _montar_resposta_por_entidade(sid), sid

        if sid:
            return _montar_resposta_filmes(sid), sid
            
        return "Não entendi bem. Tente me dizer um gênero! 🎬", sid


class AskProximoCampoAction(BotAction):
    def __init__(self, sessao_fns, deteccao_fns):
        self._detectar_valor  = deteccao_fns["detectar_valor"]

    def execute(self, contexto, sid):
        if not sid:
            return "Não temos uma sessão ativa. Me diz um gênero pra começar! 🎬", sid
            
        proximo = proximo_campo_vazio(sid)
        if not proximo:
            return "Já tenho tudo que preciso. Vou pensar numa recomendação!", sid

        valor = self._detectar_valor(proximo, contexto["tokens"], contexto["lemas"])
        if not valor:
            return f"Não entendi bem. 😅 {PERGUNTAS[proximo]}", sid

        preencher_campo(sid, proximo, valor)

        if deve_recomendar(sid):
            return "Legal! Anotado. Vou buscar algo para você...", sid

        novo_proximo = proximo_campo_vazio(sid)
        return f"Anotado! 😊 {PERGUNTAS[novo_proximo]}", sid


class ApresentarEntidadeAction(BotAction):
    def __init__(self, identificar_fn, criar_fn, encerrar_fn,
                 set_ref_fn, preencher_fn, montar_fn, set_pais_fn=None):
        self._identificar  = identificar_fn

    def execute(self, contexto, sid):
        entidade = self._identificar(contexto["nome_ref"], tipo_hint=contexto["tipo_ref"])
        if not entidade:
            return (
                f"Não encontrei **\"{contexto['nome_ref']}\"** no TMDB. 🤔\n"
                "Tente um nome diferente, ou me diga um gênero!"
            ), sid

        if sid:
            encerrar_sessao(sid)
        sid = criar_sessao()
        set_referencia(
            sid,
            entidade["tipo"],
            entidade["id"],
            entidade["nome"],
            generos=entidade.get("generos"),
            ano=entidade.get("ano"),
        )

        # Slot Filling Dinâmico
        if entidade["tipo"] == "filme" and entidade.get("generos"):
            preencher_campo(sid, "genero_pedido", entidade["generos"][0])
            # Podíamos inferir "humor" baseado no gênero pesado/leve, mas o usuário preenche depois.

        pais_ctx = contexto.get("pais")
        if pais_ctx:
            set_pais(sid, pais_ctx)

        return _montar_resposta_por_entidade(sid), sid