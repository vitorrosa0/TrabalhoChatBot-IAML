from src.nlp.pipeline import preprocessar, detectar_intencao
from src.nlp.generos import detectar_genero
from src.nlp.paises import detectar_pais
from src.nlp.referencias import detectar_referencia_texto, detectar_ator_em_mensagem_com_genero
from src.nlp.generos import tem_enfase_no_genero
from src.nlp.campos import detectar_valor_campo
from src.data.ml_recomendador import recomendar_com_ambos, salvar_exemplo, MINIMO_TREINO
from src.api.tmdb import (
    buscar_filmes_por_genero, buscar_filmes_similares,
    buscar_filmes_por_ator, buscar_filmes_por_genero_e_ator,
    identificar_entidade,
)
from src.core.session_manager import (
    criar_sessao, obter_sessao, preencher_campo,
    deve_recomendar, proximo_campo_vazio, sessao_completa,
    encerrar_sessao, adicionar_filmes_recomendados,
    filmes_ja_recomendados, PERGUNTAS,
    banir_genero, generos_banidos, travar_genero,
    genero_esta_travado, set_genero_recomendado,
    set_referencia, get_referencia, set_pais, get_pais,
)
from src.core.state import ConversationState
from src.core.action_classifier import ActionClassifier
from src.actions.registry import ActionRegistry
from src.actions.formatters import formatar_lista_filmes
from src.actions.simples import (
    SaudarAction, DespedirAction, AjudarAction,
    PedirGeneroAction, GeneroBanidoAction, FallbackAction,
)
from src.actions.recomendacao import (
    MaisFilmesAction, RecomendarAction, ApresentarEntidadeAction,
)
from src.nlp.generos import NOMES_GENEROS
from src.nlp.paises import NOMES_PAISES


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

    genero_j48, genero_lmt = recomendar_com_ambos(genero_pedido, humor, acompanhado, duracao, disposicao)

    nota_ml, genero_final = _resolver_genero_e_nota(
        genero_pedido, genero_j48, genero_lmt, banidos, genero_esta_travado(sid)
    )

    ja_vistos = filmes_ja_recomendados(sid)
    set_genero_recomendado(sid, genero_final)
    filmes    = buscar_filmes_por_genero(genero_final, quantidade=3, excluir_titulos=ja_vistos,
                                         duracao=sessao.get("duracao_preferida"), pais=pais)
    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])

    nome_genero = NOMES_GENEROS.get(genero_final, genero_final)
    nome_pais   = NOMES_PAISES.get(pais) if pais else None
    cabecalho   = (f"🎬 Aqui estão filmes {nome_pais} de **{nome_genero}**:\n\n" if nome_pais
                   else f"🎬 Aqui estão filmes de **{nome_genero}** pra você:\n\n")

    resposta = cabecalho + nota_ml + formatar_lista_filmes(filmes)

    if sessao_completa(sid):
        salvar_exemplo(genero_pedido, humor, acompanhado, duracao, disposicao, genero_final)
        encerrar_sessao(sid)
        return resposta + "Espero que curta! 🍿 Se quiser mais recomendações, é só pedir."

    proximo = proximo_campo_vazio(sid)
    return resposta + f"\n💬 {PERGUNTAS[proximo]}"


def _resolver_genero_e_nota(genero_pedido, genero_j48, genero_lmt, banidos, travado):
    if travado:
        return f"🤖 _Usando **{NOMES_GENEROS[genero_pedido]}** conforme você pediu._\n\n", genero_pedido

    notas = {
        None:                    (f"🤖 _Ainda aprendendo... usando o gênero que você pediu._\n\n", genero_pedido),
        genero_lmt:              (f"🤖 _J48 e LMT concordaram: **{NOMES_GENEROS.get(genero_j48, '')}** é o melhor para o seu perfil agora._\n\n", genero_j48),
    }
    nota_ml, genero_final = notas.get(genero_j48, (
        f"🤖 _J48 indicou **{NOMES_GENEROS.get(genero_j48, '')}** e LMT indicou **{NOMES_GENEROS.get(genero_lmt, '')}**. Usando J48._\n\n",
        genero_j48,
    ))

    if genero_final in banidos:
        return f"🤖 _O ML sugeriu um gênero que você não quer. Usando **{NOMES_GENEROS[genero_pedido]}** no lugar._\n\n", genero_pedido

    return nota_ml, genero_final


def _build_registry() -> ActionRegistry:
    registry = ActionRegistry()

    sessao_fns = {
        "obter": obter_sessao, "criar": criar_sessao, "encerrar": encerrar_sessao,
        "preencher": preencher_campo, "proximo": proximo_campo_vazio,
        "deve_recomendar": deve_recomendar, "travar": travar_genero,
        "perguntas": PERGUNTAS, "set_pais": set_pais, "get_pais": get_pais,
    }
    entidade_fns = {
        "identificar":   identificar_entidade,
        "set_ref":       set_referencia,
        "detectar_ator": detectar_ator_em_mensagem_com_genero,
    }
    montar_fns   = {"filmes": _montar_resposta_filmes, "entidade": _montar_resposta_por_entidade}
    deteccao_fns = {"tem_enfase": tem_enfase_no_genero, "detectar_valor": detectar_valor_campo}

    recomendar = RecomendarAction(sessao_fns, entidade_fns, montar_fns, deteccao_fns)

    registry.registrar("SAUDAR",              SaudarAction())
    registry.registrar("DESPEDIR",            DespedirAction(encerrar_sessao))
    registry.registrar("AJUDAR",              AjudarAction())
    registry.registrar("PEDIR_GENERO",        PedirGeneroAction())
    registry.registrar("GENERO_NEGADO",       GeneroBanidoAction())
    registry.registrar("FALLBACK",            FallbackAction())
    registry.registrar("MAIS_FILMES",         MaisFilmesAction(get_referencia, _montar_resposta_por_entidade, _montar_resposta_filmes))
    registry.registrar("RECOMENDAR",          recomendar)
    registry.registrar("RECOMENDAR_FINAL",    recomendar)
    registry.registrar("PEDIR_PROXIMO_CAMPO", recomendar)
    registry.registrar("APRESENTAR_ENTIDADE", ApresentarEntidadeAction(
        identificar_entidade, criar_sessao, encerrar_sessao,
        set_referencia, preencher_campo, _montar_resposta_por_entidade,
    ))

    return registry


_classifier = ActionClassifier()
_registry   = _build_registry()


def gerar_resposta(mensagem_usuario, sid=None):
    tokens, lemas       = preprocessar(mensagem_usuario)
    intencao            = detectar_intencao(mensagem_usuario)
    genero_afirmado, genero_negado = detectar_genero(tokens, lemas, texto_bruto=mensagem_usuario)
    tipo_ref, nome_ref  = detectar_referencia_texto(mensagem_usuario)
    pais                = detectar_pais(mensagem_usuario)

    contexto = {
        "mensagem": mensagem_usuario, "tokens": tokens, "lemas": lemas,
        "intencao": intencao, "genero_afirmado": genero_afirmado,
        "genero_negado": genero_negado, "tipo_ref": tipo_ref,
        "nome_ref": nome_ref, "pais": pais,
    }

    sessao = obter_sessao(sid) if sid else None
    if genero_negado and sid:
        banir_genero(sid, genero_negado)
        sessao = obter_sessao(sid)

    state  = ConversationState.from_session(sessao)
    action = _classifier.classify(state, intencao, contexto)
    print(f"[ActionClassifier] action={action} | campos={state.campos_preenchidos}")

    return _registry.get(action).execute(contexto, sid)