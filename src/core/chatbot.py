from __future__ import annotations

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
)
from src.data.knowledge import identificar_entidade_camadas
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
    MaisFilmesAction, SuggestMovieAction, AskProximoCampoAction, ApresentarEntidadeAction,
)
from typing import Any, Dict, Optional

from src.nlp.generos import NOMES_GENEROS
from src.nlp.paises import NOMES_PAISES


def _build_registry() -> ActionRegistry:
    registry = ActionRegistry()

    entidade_fns = {
        "identificar":   identificar_entidade_camadas,
        "detectar_ator": detectar_ator_em_mensagem_com_genero,
    }
    deteccao_fns = {"tem_enfase": tem_enfase_no_genero, "detectar_valor": detectar_valor_campo}

    # Passamos None para os antigos montar_fns e sessao_fns, pois as Actions agora importam diretamente o SessionManager
    recomendar_action  = SuggestMovieAction(None, entidade_fns, None, deteccao_fns)
    pedir_campo_action = AskProximoCampoAction(None, deteccao_fns)

    registry.registrar("SAUDAR",              SaudarAction())
    registry.registrar("DESPEDIR",            DespedirAction(encerrar_sessao))
    registry.registrar("AJUDAR",              AjudarAction())
    registry.registrar("PEDIR_GENERO",        PedirGeneroAction())
    registry.registrar("GENERO_NEGADO",       GeneroBanidoAction())
    registry.registrar("FALLBACK",            FallbackAction())
    registry.registrar("MAIS_FILMES",         MaisFilmesAction())
    registry.registrar("RECOMENDAR",          recomendar_action)
    registry.registrar("RECOMENDAR_FINAL",    recomendar_action)
    registry.registrar("PEDIR_PROXIMO_CAMPO", pedir_campo_action)
    registry.registrar("APRESENTAR_ENTIDADE", ApresentarEntidadeAction(identificar_entidade_camadas, None, None, None, None, None))

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