from nltk.tokenize import word_tokenize
from src.nlp.pipeline import lematizar
from src.nlp.filmes import MAPA_GENEROS

PALAVRAS_NEGACAO = {"não", "nao", "nem", "nunca", "jamais", "tampouco"}

NOMES_GENEROS = {
    "acao": "Ação", "comedia": "Comédia", "drama": "Drama",
    "terror": "Terror", "romance": "Romance",
    "ficcao_cientifica": "Ficção Científica",
    "animacao": "Animação", "suspense": "Suspense",
}

LEMAS_GENEROS = {
    genero: [lematizar(p) for p in palavras]
    for genero, palavras in MAPA_GENEROS.items()
}

def detectar_genero(tokens, lemas, texto_bruto=""):
    tokens_brutos   = word_tokenize(texto_bruto.lower(), language="portuguese")
    genero_afirmado = None
    genero_negado   = None

    for genero, lemas_genero in LEMAS_GENEROS.items():
        for i, token_bruto in enumerate(tokens_brutos):
            lema_token = lematizar(token_bruto)
            pertence   = lema_token in lemas_genero or token_bruto in MAPA_GENEROS[genero]
            if pertence:
                inicio   = max(0, i - 3)
                contexto = tokens_brutos[inicio:i]
                if any(neg in contexto for neg in PALAVRAS_NEGACAO):
                    genero_negado = genero
                else:
                    genero_afirmado = genero
                break

    return genero_afirmado, genero_negado

def tem_enfase_no_genero(texto_bruto: str, genero_pedido: str) -> bool:
    tokens_brutos = word_tokenize(texto_bruto.lower(), language="portuguese")
    lemas_genero  = LEMAS_GENEROS.get(genero_pedido, [])

    tem_genero = any(
        lematizar(t) in lemas_genero or t in MAPA_GENEROS.get(genero_pedido, [])
        for t in tokens_brutos
    )
    if not tem_genero:
        return False

    ENFASE_SIMPLES = {"só", "so", "apenas", "somente", "prefiro", "insisto"}
    tem_enfase = any(p in tokens_brutos for p in ENFASE_SIMPLES)
    bigrams    = [f"{tokens_brutos[i]} {tokens_brutos[i+1]}" for i in range(len(tokens_brutos) - 1)]
    ENFASE_BIGRAM = {"quero apenas", "só quero", "quero só", "quero somente"}
    return tem_enfase or any(b in bigrams for b in ENFASE_BIGRAM)