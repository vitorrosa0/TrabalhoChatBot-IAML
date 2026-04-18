from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ConversationState:
    tem_genero:      bool = False
    tem_humor:       bool = False
    tem_acompanhado: bool = False
    tem_duracao:     bool = False
    tem_disposicao:  bool = False
    tem_semente:     bool = False  # filme ou ator de referência
    campos_preenchidos: int = 0
    genero_travado:  bool = False
    tem_banidos:     bool = False

    @classmethod
    def from_session(cls, sessao: Optional[dict]) -> "ConversationState":
        if not sessao:
            return cls()
        return cls(
            tem_genero      = sessao.get("genero_pedido")      is not None,
            tem_humor       = sessao.get("humor")              is not None,
            tem_acompanhado = sessao.get("acompanhado")        is not None,
            tem_duracao     = sessao.get("duracao_preferida")  is not None,
            tem_disposicao  = sessao.get("disposicao")         is not None,
            tem_semente     = sessao.get("referencia")         is not None,
            campos_preenchidos = sum([
                sessao.get("genero_pedido")     is not None,
                sessao.get("humor")             is not None,
                sessao.get("acompanhado")       is not None,
                sessao.get("duracao_preferida") is not None,
                sessao.get("disposicao")        is not None,
            ]),
            genero_travado  = sessao.get("genero_travado", False),
            tem_banidos     = bool(sessao.get("generos_banidos")),
        )