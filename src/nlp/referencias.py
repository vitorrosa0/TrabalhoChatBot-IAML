import re
from src.nlp.pipeline import lematizar

_RE_FILME_SIMILAR = [
    re.compile(r"\balgo\s+(?:como|tipo|parecido\s+com|similar\s+a|igual\s+a)\s+(.+)", re.I),
    re.compile(r"\bparecido\s+com\s+(.+)",                                         re.I),
    re.compile(r"\bsimilar\s+a(?:o|os|as)?\s+(.+)",                               re.I),
    re.compile(r"\bsemelhante\s+a(?:o|os|as)?\s+(.+)",                            re.I),
    re.compile(r"\bno\s+estilo\s+(?:de|do|da)\s+(.+)",                            re.I),
    re.compile(r"\bestilo\s+(?:de|do|da|dos|das)\s+(.+)",                         re.I),
    re.compile(r"\bigual\s+a(?:o)?\s+(.+)",                                        re.I),
    re.compile(r"\bcomo\s+o\s+filme\s+(.+)",                                       re.I),
    re.compile(r"\bum\s+filme\s+(?:como|tipo)\s+(.+)",                            re.I),
    re.compile(r"\btipo\s+o\s+filme\s+(.+)",                                       re.I),
    re.compile(r"\bfilme\s+.{2,80}?\s+tipo\s+(.+?)(?:\s*[.,!?]|$)",              re.I),
    re.compile(r"\btipo\s+([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-]{1,50}?)(?:\s*[.,!?]|$)", re.I),
]

_RE_INQUIRY = [
    re.compile(
        r"\b(?:você|voce)\s+(?:já\s+|ja\s+)?conhece\s+(?:o\s+)?(?:filme\s+)?(.+)",
        re.I,
    ),
    re.compile(r"\bconhece\s+(?:o\s+)?(?:filme\s+)?(.+)", re.I),
    re.compile(r"\bsabe\s+se\s+(?:tem|existe)\s+(?:o\s+)?(?:filme\s+)?(.+)", re.I),
    re.compile(
        r"\b(?:já\s+|ja\s+)?ouviu\s+falar\s+(?:de|do|da|dos|das)\s+(?:o\s+)?(?:filme\s+)?(.+)",
        re.I,
    ),
    re.compile(r"\bjá\s+viu\s+(?:o\s+)?(?:filme\s+)?(.+)", re.I),
]

_RE_PESSOA = [
    re.compile(r"\bfilmes?\s+com\s+(?:o\s+(?:ator|diretor|cineasta|realizador)\s+|a\s+(?:atriz|diretora|cineasta)\s+|o\s+|a\s+)?(.+)", re.I),
    re.compile(r"\bfilmes?\s+d[ao]s?\s+(?:(?:ator|atriz|diretor|diretora|cineasta|realizador)\s+)?(.+)", re.I),
    re.compile(r"\bcom\s+(?:o\s+(?:ator|diretor|cineasta)|a\s+(?:atriz|diretora|cineasta))\s+(.+)", re.I),
    re.compile(r"\b(?:dirigido|estrelado|protagonizado|realizado)\s+por\s+(.+)",   re.I),
]

_RE_CARGO_PREFIXO = re.compile(
    r"^(?:o\s+|a\s+)?(?:diretor|diretora|ator|atriz|cineasta|realizador|roteirista|produtor|produtora)\s+",
    re.I,
)

_RE_ATOR_APOS_GENERO = re.compile(
    r"\bcom\s+(?:o\s+|a\s+)?([A-Za-zÀ-ÿ]{2,}(?:\s+[A-Za-zÀ-ÿ]{2,})+)",
    re.I,
)

_PREFIXOS_INVALIDOS_TITULO = frozenset(
    {"de", "do", "da", "dos", "das", "um", "uma", "uns", "umas", "meu", "minha"}
)


def _titulo_candidato_valido(nome: str) -> bool:
    partes = nome.split()
    if not partes:
        return False
    if partes[0].lower() in _PREFIXOS_INVALIDOS_TITULO:
        return False
    return True


_NOMES_NAO_ATOR = {
    "amigos","amigo","amiga","familia","família","filhos","casal",
    "namorado","namorada","parceiro","parceira","esposo","esposa",
    "sozinho","galera","turma","pessoal","legenda","dublagem",
}

def _limpar_titulo_candidato(raw: str) -> str:
    nome = raw.strip().rstrip(".,!?")
    for prefix in ("o filme ", "a série ", "serie "):
        if nome.lower().startswith(prefix):
            nome = nome[len(prefix) :].strip()
    return nome


def detectar_referencia_texto(texto: str):
    for pattern in _RE_FILME_SIMILAR:
        m = pattern.search(texto)
        if m:
            nome = _limpar_titulo_candidato(m.group(1))
            if nome and nome.lower() not in {"filme", "um", "de", "tipo"} and _titulo_candidato_valido(nome):
                return "filme", nome
    for pattern in _RE_INQUIRY:
        m = pattern.search(texto)
        if m:
            nome = _limpar_titulo_candidato(m.group(1))
            if nome and _titulo_candidato_valido(nome):
                return "filme", nome
    for pattern in _RE_PESSOA:
        m = pattern.search(texto)
        if m:
            nome = _RE_CARGO_PREFIXO.sub("", m.group(1).strip().rstrip(".,!?")).strip()
            if nome:
                return "ator", nome
    return None, None

def detectar_ator_em_mensagem_com_genero(texto: str):
    m = _RE_ATOR_APOS_GENERO.search(texto)
    if m:
        candidato = m.group(1).strip().rstrip(".,!?")
        if candidato.lower() not in _NOMES_NAO_ATOR:
            return candidato
    return None