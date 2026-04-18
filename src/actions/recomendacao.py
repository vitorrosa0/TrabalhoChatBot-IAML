from typing import Optional
from src.actions.base import BotAction
from src.actions.formatters import formatar_lista_filmes
from src.nlp.generos import NOMES_GENEROS
from src.nlp.paises import NOMES_PAISES


class MaisFilmesAction(BotAction):
    def __init__(self, get_referencia_fn, montar_entidade_fn, montar_filmes_fn):
        self._get_ref         = get_referencia_fn
        self._montar_entidade = montar_entidade_fn
        self._montar_filmes   = montar_filmes_fn

    def execute(self, contexto, sid):
        if not sid:
            return "Não temos uma conversa ativa. Me diz um gênero pra começar! 🎬", sid
        montar = self._montar_entidade if self._get_ref(sid) else self._montar_filmes
        return montar(sid), sid


class RecomendarAction(BotAction):
    def __init__(self, sessao_fns, entidade_fns, montar_fns, deteccao_fns):
        self._obter_sessao    = sessao_fns["obter"]
        self._criar_sessao    = sessao_fns["criar"]
        self._encerrar_sessao = sessao_fns["encerrar"]
        self._preencher_campo = sessao_fns["preencher"]
        self._proximo_campo   = sessao_fns["proximo"]
        self._deve_recomendar = sessao_fns["deve_recomendar"]
        self._travar          = sessao_fns["travar"]
        self._set_pais        = sessao_fns["set_pais"]
        self.PERGUNTAS        = sessao_fns["perguntas"]

        self._identificar_entidade = entidade_fns["identificar"]
        self._set_referencia       = entidade_fns["set_ref"]
        self._detectar_ator        = entidade_fns["detectar_ator"]

        self._montar_filmes   = montar_fns["filmes"]
        self._montar_entidade = montar_fns["entidade"]

        self._tem_enfase      = deteccao_fns["tem_enfase"]
        self._detectar_valor  = deteccao_fns["detectar_valor"]

    def execute(self, contexto, sid):
        genero_afirmado = contexto.get("genero_afirmado")
        if genero_afirmado:
            return self._handle_genero(contexto, sid)
        if sid:
            return self._handle_campo(contexto, sid)
        return "Não entendi. Me diz um gênero! 🎬", sid

    def _handle_genero(self, contexto, sid):
        genero    = contexto["genero_afirmado"]
        mensagem  = contexto["mensagem"]
        tipo_ref  = contexto.get("tipo_ref")
        nome_ref  = contexto.get("nome_ref")
        pais      = contexto.get("pais")

        sessao       = self._obter_sessao(sid) if sid else None
        genero_atual = sessao.get("genero_pedido") if sessao else None

        if sid and genero == genero_atual:
            if self._tem_enfase(mensagem, genero):
                self._travar(sid)
                return (
                    f"Entendido! Vou te recomendar apenas **{NOMES_GENEROS[genero]}** daqui pra frente. 🎬\n\n"
                    + self._montar_filmes(sid)
                ), sid
            return self._montar_filmes(sid), sid

        if sid:
            self._encerrar_sessao(sid)
        sid = self._criar_sessao()
        self._preencher_campo(sid, "genero_pedido", genero)
        if pais:
            self._set_pais(sid, pais)

        candidato = nome_ref if tipo_ref == "ator" else self._detectar_ator(mensagem)
        if candidato:
            entidade = self._identificar_entidade(candidato, tipo_hint="ator")
            if entidade:
                self._set_referencia(sid, "ator", entidade["id"], entidade["nome"])
                return self._montar_entidade(sid), sid

        return self._montar_filmes(sid), sid

    def _handle_campo(self, contexto, sid):
        proximo = self._proximo_campo(sid)
        if not proximo:
            return self._montar_filmes(sid), sid

        valor = self._detectar_valor(proximo, contexto["tokens"], contexto["lemas"])
        if not valor:
            return f"Não entendi bem. 😅 {self.PERGUNTAS[proximo]}", sid

        self._preencher_campo(sid, proximo, valor)

        if self._deve_recomendar(sid):
            return self._montar_filmes(sid), sid

        novo_proximo = self._proximo_campo(sid)
        return f"Anotado! 😊 {self.PERGUNTAS[novo_proximo]}", sid


class ApresentarEntidadeAction(BotAction):
    def __init__(self, identificar_fn, criar_fn, encerrar_fn,
                 set_ref_fn, preencher_fn, montar_fn):
        self._identificar  = identificar_fn
        self._criar        = criar_fn
        self._encerrar     = encerrar_fn
        self._set_ref      = set_ref_fn
        self._preencher    = preencher_fn
        self._montar       = montar_fn

    def execute(self, contexto, sid):
        entidade = self._identificar(contexto["nome_ref"], tipo_hint=contexto["tipo_ref"])
        if not entidade:
            return (
                f"Não encontrei **\"{contexto['nome_ref']}\"** no TMDB. 🤔\n"
                "Tente um nome diferente, ou me diga um gênero!"
            ), sid

        if sid:
            self._encerrar(sid)
        sid = self._criar()
        self._set_ref(sid, entidade["tipo"], entidade["id"], entidade["nome"])

        if entidade["tipo"] == "filme" and entidade.get("generos"):
            self._preencher(sid, "genero_pedido", entidade["generos"][0])

        return self._montar(sid), sid