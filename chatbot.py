import re
import string
import simplemma
import nltk

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.classify import NaiveBayesClassifier
from nltk.classify.util import accuracy

from filmes import MAPA_GENEROS
from ml_recomendador import recomendar_com_ambos, salvar_exemplo, MINIMO_TREINO
from tmdb_api import (
    buscar_filmes_por_genero,
    buscar_filmes_similares,
    buscar_filmes_por_ator,
    buscar_filmes_por_genero_e_ator,
    identificar_entidade,
)
from session_manager import (
    criar_sessao, obter_sessao, preencher_campo,
    deve_recomendar, proximo_campo_vazio, sessao_completa,
    encerrar_sessao, adicionar_filmes_recomendados,
    filmes_ja_recomendados, campos_preenchidos, PERGUNTAS,
    banir_genero, generos_banidos, travar_genero,
    genero_esta_travado, destravar_genero,
    set_genero_recomendado, get_genero_recomendado,
    set_referencia, get_referencia,
    set_pais, get_pais,
)

STOPWORDS_PT = set(stopwords.words("portuguese"))

PALAVRAS_NEGACAO = {"não", "nao", "nem", "nunca", "jamais", "tampouco"}
PALAVRAS_ENFASE  = {"só", "so", "apenas", "somente", "somente", "prefiro", "insisto", "quero apenas", "só quero"}

def lematizar(palavra):
    return simplemma.lemmatize(palavra, lang="pt")


DADOS_TREINO_BRUTOS = [
    ("oi", "saudacao"), ("olá", "saudacao"), ("ola", "saudacao"),
    ("oi tudo bem", "saudacao"), ("hey", "saudacao"), ("bom dia", "saudacao"),
    ("boa tarde", "saudacao"), ("boa noite", "saudacao"), ("salve", "saudacao"),
    ("opa", "saudacao"), ("e aí", "saudacao"), ("e ai tudo certo", "saudacao"),
    ("olá como vai", "saudacao"), ("oi boa tarde", "saudacao"),
    ("hey tudo bem", "saudacao"), ("salve salve", "saudacao"),
    ("boas", "saudacao"), ("oi sumido", "saudacao"),

    ("tchau", "despedida"), ("até mais", "despedida"), ("adeus", "despedida"),
    ("valeu", "despedida"), ("obrigado", "despedida"), ("obrigada", "despedida"),
    ("até logo", "despedida"), ("foi bom falar", "despedida"),
    ("encerrando", "despedida"), ("quero sair", "despedida"),
    ("vou encerrar", "despedida"), ("até amanhã", "despedida"),
    ("muito obrigado pela ajuda", "despedida"), ("valeu mesmo", "despedida"),
    ("flw", "despedida"), ("até", "despedida"), ("encerrar conversa", "despedida"),

    ("como funciona", "ajuda"), ("como usar", "ajuda"), ("me ajuda", "ajuda"),
    ("o que você faz", "ajuda"), ("o que você pode fazer", "ajuda"),
    ("preciso de ajuda", "ajuda"), ("help", "ajuda"),
    ("como faço para", "ajuda"), ("não sei como usar", "ajuda"),
    ("pode me explicar", "ajuda"), ("quais são as opções", "ajuda"),
    ("o que posso pedir", "ajuda"), ("como funciona isso", "ajuda"),
    ("me explica", "ajuda"), ("tem tutorial", "ajuda"), ("instruções", "ajuda"),

    ("quero um filme", "recomendacao"), ("me recomenda um filme", "recomendacao"),
    ("sugere algum filme", "recomendacao"), ("indica um filme", "recomendacao"),
    ("quero assistir algo", "recomendacao"), ("me mostra um filme", "recomendacao"),
    ("quero ver um filme", "recomendacao"), ("me sugere algo", "recomendacao"),
    ("qual filme devo assistir", "recomendacao"),
    ("tem algum filme bom", "recomendacao"),
    ("me indica algo para ver hoje", "recomendacao"),
    ("quero uma recomendação", "recomendacao"), ("o que assistir", "recomendacao"),
    ("me dá uma dica de filme", "recomendacao"),
    ("que filme você recomenda", "recomendacao"),
    ("preciso de indicação de filme", "recomendacao"),

    ("manda mais", "mais_filmes"), ("quero mais", "mais_filmes"),
    ("mais 3", "mais_filmes"), ("outros filmes", "mais_filmes"),
    ("me manda outros", "mais_filmes"), ("recomende mais", "mais_filmes"),
    ("mais filmes", "mais_filmes"), ("outros 3", "mais_filmes"),
    ("me dá mais", "mais_filmes"), ("mais opções", "mais_filmes"),
    ("não gostei manda outros", "mais_filmes"), ("tem mais", "mais_filmes"),
    ("quero ver outros", "mais_filmes"), ("manda diferentes", "mais_filmes"),
]

NOMES_GENEROS = {
    "acao":              "Ação",
    "aventura":          "Aventura",
    "animacao":          "Animação",
    "cinema_tv":         "Cinema TV",
    "comedia":           "Comédia",
    "crime":             "Crime",
    "documentario":      "Documentário",
    "drama":             "Drama",
    "familia":           "Família",
    "fantasia":          "Fantasia",
    "faroeste":          "Faroeste",
    "ficcao_cientifica": "Ficção Científica",
    "guerra":            "Guerra",
    "historia":          "História",
    "misterio":          "Mistério",
    "musica":            "Música",
    "romance":           "Romance",
    "suspense":          "Suspense",
    "terror":            "Terror",
}


def _extrair_features(texto):
    texto = texto.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    lemas  = [lematizar(t) for t in tokens]
    return {f"lema_{l}": True for l in lemas}

_dados_formatados = [(_extrair_features(f), i) for f, i in DADOS_TREINO_BRUTOS]
classificador_intencao = NaiveBayesClassifier.train(_dados_formatados)
_acuracia = accuracy(classificador_intencao, _dados_formatados)
print(f"[NaiveBayes] Classificador treinado. Acurácia no treino: {_acuracia:.1%}")


LEMAS_GENEROS = {
    genero: [lematizar(p) for p in palavras]
    for genero, palavras in MAPA_GENEROS.items()
}

LEMAS_HUMOR = {
    "animado":   [lematizar(p) for p in ["animado","empolgado","energia","agitado","feliz","bem","otimo","ótimo"]],
    "calmo":     [lematizar(p) for p in ["calmo","relaxado","tranquilo","sossegado","descansando"]],
    "entediado": [lematizar(p) for p in ["entediado","tedio","chato","sem","fazer","enfadado"]],
    "assustado": [lematizar(p) for p in ["assustado","medo","nervoso","tenso","ansioso"]],
    "romantico": [lematizar(p) for p in ["romantico","apaixonado","amor","namorado","namorada","sentimental"]],
    "curioso":   [lematizar(p) for p in ["curioso","pensativo","refletindo","interessado","intrigado"]],
    "triste":    [lematizar(p) for p in ["triste","melancólico","melancolico","mal","deprimido","chateado"]],
}

LEMAS_ACOMPANHADO = {
    "sozinho": [lematizar(p) for p in ["sozinho","solo","so"]],
    "amigos":  [lematizar(p) for p in ["amigos","amigo","galera","turma","pessoal","amiga"]],
    "casal":   [lematizar(p) for p in ["casal","namorado","namorada","esposo","esposa","parceiro","parceira"]],
    "familia": [lematizar(p) for p in ["familia","filho","filha","pai","mae","crianca","filhos", "família"]],
}

LEMAS_DURACAO = {
    "curto": [lematizar(p) for p in ["curto","rapido","rápido","pequeno","pouco","curtinho","90"]],
    "medio": [lematizar(p) for p in ["medio","médio","normal","moderado","tanto"]],
    "longo": [lematizar(p) for p in ["longo","longa","demorado","grande","muito","comprido","2h","3h"]],
}

LEMAS_DISPOSICAO = {
    "pensar": [lematizar(p) for p in ["pensar","refletir","profundo","inteligente","complexo","denso","cerebral"]],
    "curtir": [lematizar(p) for p in ["curtir","desligar","relaxar","entretenimento","leve","divertir","besteira"]],
}

MAPA_PAISES = {
    "BR": ["brasileiro","brasileira","brasileiros","brasileiras","brasil"],
    "US": ["americano","americana","americanos","americanas","eua","hollywood"],
    "FR": ["francês","frances","francesa","franceses","francesas","franca","franca"],
    "ES": ["espanhol","espanhola","espanhóis","espanhois","espanholas","espanha"],
    "IT": ["italiano","italiana","italianos","italianas","italia"],
    "JP": ["japonês","japones","japonesa","japoneses","japonesas","japao","japão","anime"],
    "KR": ["coreano","coreana","coreanos","coreanas","coreia","sul-coreano"],
    "MX": ["mexicano","mexicana","mexicanos","mexicanas","mexico","méxico"],
    "AR": ["argentino","argentina","argentinos","argentinas"],
    "IN": ["indiano","indiana","indianos","indianas","bollywood"],
}

NOMES_PAISES = {
    "BR": "brasileiros", "US": "americanos", "FR": "franceses",
    "ES": "espanhóis",   "IT": "italianos",  "JP": "japoneses",
    "KR": "coreanos",    "MX": "mexicanos",  "AR": "argentinos", "IN": "indianos",
}

LEMAS_PAISES = {
    codigo: [lematizar(p) for p in palavras]
    for codigo, palavras in MAPA_PAISES.items()
}


def detectar_pais(texto_bruto):
    tokens_brutos = word_tokenize(texto_bruto.lower(), language="portuguese")
    for codigo, lemas_pais in LEMAS_PAISES.items():
        palavras_pais = MAPA_PAISES[codigo]
        for token_bruto in tokens_brutos:
            lema_token = lematizar(token_bruto)
            if lema_token in lemas_pais or token_bruto in palavras_pais:
                return codigo
    return None


_RE_FILME_SIMILAR = [
    re.compile(r"\balgo\s+(?:como|parecido\s+com|similar\s+a|igual\s+a)\s+(.+)",           re.I),
    re.compile(r"\bparecido\s+com\s+(.+)",                                                  re.I),
    re.compile(r"\bsimilar\s+a(?:o|os|as)?\s+(.+)",                                        re.I),
    re.compile(r"\bsemelhante\s+a(?:o|os|as)?\s+(.+)",                                     re.I),
    re.compile(r"\bno\s+estilo\s+(?:de|do|da)\s+(.+)",                                     re.I),
    re.compile(r"\bestilo\s+(?:de|do|da|dos|das)\s+(.+)",                                  re.I),
    re.compile(r"\bigual\s+a(?:o)?\s+(.+)",                                                 re.I),
    re.compile(r"\bcomo\s+o\s+filme\s+(.+)",                                                re.I),
    re.compile(r"\bum\s+filme\s+(?:como|tipo)\s+(.+)",                                     re.I),
    re.compile(r"\btipo\s+o\s+filme\s+(.+)",                                                re.I),
]

_RE_PESSOA = [
    re.compile(r"\bfilmes?\s+com\s+(?:o\s+(?:ator|diretor|cineasta|realizador)\s+|a\s+(?:atriz|diretora|cineasta)\s+|o\s+|a\s+)?(.+)", re.I),
    re.compile(r"\bfilmes?\s+d[ao]s?\s+(?:(?:ator|atriz|diretor|diretora|cineasta|realizador)\s+)?(.+)", re.I),
    re.compile(r"\bcom\s+(?:o\s+(?:ator|diretor|cineasta)|a\s+(?:atriz|diretora|cineasta))\s+(.+)", re.I),
    re.compile(r"\b(?:dirigido|estrelado|protagonizado|realizado)\s+por\s+(.+)",             re.I),
]

_RE_CARGO_PREFIXO = re.compile(
    r"^(?:o\s+|a\s+)?(?:diretor|diretora|ator|atriz|cineasta|realizador|roteirista|produtor|produtora)\s+",
    re.I,
)

_RE_ATOR_APOS_GENERO = re.compile(
    r"\bcom\s+(?:o\s+|a\s+)?([A-Za-zÀ-ÿ]{2,}(?:\s+[A-Za-zÀ-ÿ]{2,})+)",
    re.I,
)
_NOMES_NAO_ATOR = {
    "amigos", "amigo", "amiga", "familia", "família", "filhos", "casal",
    "namorado", "namorada", "parceiro", "parceira", "esposo", "esposa",
    "sozinho", "galera", "turma", "pessoal", "legenda", "dublagem",
}


def _limpar_nome_pessoa(nome):
    return _RE_CARGO_PREFIXO.sub("", nome).strip()


def _detectar_ator_em_mensagem_com_genero(texto):
    m = _RE_ATOR_APOS_GENERO.search(texto)
    if m:
        candidato = m.group(1).strip().rstrip(".,!?")
        if candidato.lower() not in _NOMES_NAO_ATOR:
            return candidato
    return None


def _detectar_referencia_texto(texto):
    texto = texto.strip()

    for pattern in _RE_FILME_SIMILAR:
        m = pattern.search(texto)
        if m:
            nome = m.group(1).strip().rstrip(".,!?")
            if nome:
                return "filme", nome

    for pattern in _RE_PESSOA:
        m = pattern.search(texto)
        if m:
            nome = _limpar_nome_pessoa(m.group(1).strip().rstrip(".,!?"))
            if nome:
                return "ator", nome

    return None, None


def preprocessar(texto):
    texto = texto.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    lemas = [lematizar(t) for t in tokens]
    return tokens, lemas

def detectar_intencao(texto_original):
    features = _extrair_features(texto_original)
    if not features:
        return "desconhecida"
    intencao = classificador_intencao.classify(features)
    dist     = classificador_intencao.prob_classify(features)
    prob     = dist.prob(intencao)
    print(f"[NaiveBayes] Intenção: '{intencao}' (confiança: {prob:.1%})")
    return intencao if prob >= 0.35 else "desconhecida"

def detectar_genero(tokens, lemas, texto_bruto=""):
    tokens_brutos = word_tokenize(texto_bruto.lower(), language="portuguese")

    genero_afirmado = None
    genero_negado   = None

    for genero, lemas_genero in LEMAS_GENEROS.items():
        for i, token_bruto in enumerate(tokens_brutos):
            lema_token = lematizar(token_bruto)
            pertence_ao_genero = (
                lema_token in lemas_genero or
                token_bruto in MAPA_GENEROS[genero]
            )
            if pertence_ao_genero:
                inicio   = max(0, i - 3)
                contexto = tokens_brutos[inicio:i]
                if any(neg in contexto for neg in PALAVRAS_NEGACAO):
                    print(f"[Negação] Gênero '{genero}' negado. Contexto: {contexto}")
                    genero_negado = genero
                else:
                    genero_afirmado = genero
                break

    return genero_afirmado, genero_negado

def _tem_enfase_no_genero(texto_bruto, genero_pedido):
    tokens_brutos = word_tokenize(texto_bruto.lower(), language="portuguese")
    lemas_genero  = LEMAS_GENEROS.get(genero_pedido, [])

    tem_genero_pedido = any(
        lematizar(t) in lemas_genero or t in MAPA_GENEROS.get(genero_pedido, [])
        for t in tokens_brutos
    )
    if not tem_genero_pedido:
        return False

    ENFASE_SIMPLES = {"só", "so", "apenas", "somente", "prefiro", "insisto"}
    tem_enfase = any(p in tokens_brutos for p in ENFASE_SIMPLES)

    bigrams = [f"{tokens_brutos[i]} {tokens_brutos[i+1]}" for i in range(len(tokens_brutos)-1)]
    ENFASE_BIGRAM = {"quero apenas", "só quero", "quero só", "quero somente"}
    tem_enfase = tem_enfase or any(b in bigrams for b in ENFASE_BIGRAM)

    return tem_enfase

def _detectar_valor_campo(campo, tokens, lemas):
    mapa = {
        "humor":             LEMAS_HUMOR,
        "acompanhado":       LEMAS_ACOMPANHADO,
        "duracao_preferida": LEMAS_DURACAO,
        "disposicao":        LEMAS_DISPOSICAO,
    }
    opcoes = mapa.get(campo, {})
    for valor, lemas_valor in opcoes.items():
        for lema in lemas:
            if lema in lemas_valor:
                return valor
    return None

def _formatar_lista_filmes(filmes):
    resultado = ""
    for i, filme in enumerate(filmes, 1):
        estrelas    = f" ⭐ {filme['nota']}/10" if filme.get("nota") else ""
        duracao_min = filme.get("duracao_min")
        if duracao_min:
            horas = duracao_min // 60
            mins  = duracao_min % 60
            info_duracao = f" ⏱ {horas} h {mins} min" if horas else f" ⏱ {mins} min"
        else:
            info_duracao = ""
        plataformas = filme.get("plataformas", [])
        resultado += f"{i}. **{filme['titulo']}** ({filme['ano']}){estrelas}{info_duracao}\n"
        if plataformas:
            plat_encoded = "|".join(f"{p['nome']}={p['logo']}" for p in plataformas)
            resultado += f"   [PLATFORMS:{plat_encoded}]\n"
        resultado += f"   _{filme['descricao']}_\n\n"
    return resultado


def _montar_resposta_por_entidade(sid):
    sessao    = obter_sessao(sid)
    ref       = get_referencia(sid)
    genero    = sessao.get("genero_pedido")
    ja_vistos = filmes_ja_recomendados(sid)

    if ref["tipo"] == "filme":
        generos_filme = ref.get("generos", [])
        filmes = buscar_filmes_similares(
            ref["id"],
            generos_filme=generos_filme,
            quantidade=3,
            excluir_titulos=ja_vistos,
        )
        ano_str = f" ({ref['ano']})" if ref.get("ano") else ""
        intro   = f"🎬 Baseado em **{ref['nome']}{ano_str}**, aqui estão filmes que você pode gostar:\n\n"

    elif ref["tipo"] == "ator" and genero:
        nome_genero = NOMES_GENEROS.get(genero, genero)
        filmes = buscar_filmes_por_genero_e_ator(
            genero, ref["id"], quantidade=3, excluir_titulos=ja_vistos
        )
        if filmes:
            intro = f"🎬 Filmes de **{nome_genero}** com **{ref['nome']}**:\n\n"
        else:
            filmes = buscar_filmes_por_ator(ref["id"], quantidade=3, excluir_titulos=ja_vistos)
            intro  = (
                f"🎬 Não encontrei filmes de {nome_genero} com **{ref['nome']}**. "
                f"Mas separei outros dele(a):\n\n"
            )

    else:
        filmes = buscar_filmes_por_ator(ref["id"], quantidade=3, excluir_titulos=ja_vistos)
        intro  = f"🎬 Aqui estão filmes com **{ref['nome']}**:\n\n"

    if not filmes:
        return (
            f"Hmm, não encontrei filmes para **{ref['nome']}** no momento. 😅\n"
            "Tente me dizer um gênero ou outro nome!"
        )

    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])

    resposta  = intro
    resposta += _formatar_lista_filmes(filmes)
    resposta += "Se quiser mais, é só pedir! 😊"
    return resposta


def _montar_resposta_filmes(sid):
    sessao = obter_sessao(sid)
    pais = get_pais(sid)

    genero_pedido = sessao.get("genero_pedido")

    if pais and not genero_pedido:
        ja_vistos = filmes_ja_recomendados(sid)
        nome_pais = NOMES_PAISES.get(pais, pais)
        filmes = buscar_filmes_por_genero(
            None,
            quantidade=3,
            excluir_titulos=ja_vistos,
            duracao=sessao.get("duracao_preferida"),
            pais=pais,
        )
        if not filmes:
            return "Hmm, não encontrei filmes para esse país no momento. 😅 Tente pedir um gênero também!"
        adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])
        resposta  = f"🎬 Aqui estão filmes {nome_pais} para você:\n\n"
        resposta += _formatar_lista_filmes(filmes)
        resposta += "Se quiser mais ou um gênero específico, é só pedir! 😊"
        return resposta

    humor         = sessao.get("humor") or "calmo"
    acompanhado   = sessao.get("acompanhado") or "sozinho"
    duracao       = sessao.get("duracao_preferida") or "medio"
    disposicao    = sessao.get("disposicao") or "curtir"
    banidos       = generos_banidos(sid)
    travado       = genero_esta_travado(sid)

    if travado:
        genero_final = genero_pedido
        nota_ml = f"🤖 _Usando **{NOMES_GENEROS[genero_final]}** conforme você pediu._\n\n"
    else:
        genero_j48, genero_lmt = recomendar_com_ambos(
            genero_pedido, humor, acompanhado, duracao, disposicao
        )

        if genero_j48 is None:
            genero_final = genero_pedido
            nota_ml = (
                f"🤖 _Ainda aprendendo... usando o gênero que você pediu. "
                f"({MINIMO_TREINO} interações necessárias para ativar o ML)_\n\n"
            )
        elif genero_j48 == genero_lmt:
            genero_final = genero_j48
            nota_ml = (
                f"🤖 _J48 e LMT concordaram: **{NOMES_GENEROS[genero_final]}** "
                f"é o melhor para o seu perfil agora._\n\n"
            )
        else:
            genero_final = genero_j48
            nota_ml = (
                f"🤖 _J48 indicou **{NOMES_GENEROS[genero_j48]}** e "
                f"LMT indicou **{NOMES_GENEROS[genero_lmt]}**. "
                f"Usando J48 (maior acurácia no experimento)._\n\n"
            )

        if genero_final in banidos:
            print(f"[Banido] ML sugeriu '{genero_final}' que está banido. Usando '{genero_pedido}'.")
            genero_final = genero_pedido
            nota_ml = (
                f"🤖 _O ML sugeriu um gênero que você não quer. "
                f"Usando **{NOMES_GENEROS[genero_final]}** no lugar._\n\n"
            )

    ja_vistos = filmes_ja_recomendados(sid)
    set_genero_recomendado(sid, genero_final)
    filmes = buscar_filmes_por_genero(
        genero_final,
        quantidade=3,
        excluir_titulos=ja_vistos,
        duracao=sessao.get("duracao_preferida"),
        pais=pais,
    )
    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])

    nome_genero = NOMES_GENEROS.get(genero_final, genero_final)
    nome_pais   = NOMES_PAISES.get(pais) if pais else None
    if nome_pais:
        resposta = f"🎬 Aqui estão filmes {nome_pais} de **{nome_genero}**:\n\n"
    else:
        resposta = f"🎬 Aqui estão filmes de **{nome_genero}** pra você:\n\n"
    resposta   += _formatar_lista_filmes(filmes)
    resposta   += nota_ml

    if sessao_completa(sid):
        salvar_exemplo(genero_pedido, humor, acompanhado, duracao, disposicao, genero_final)
        encerrar_sessao(sid)
        resposta += "Espero que curta! 🍿 Se quiser mais recomendações, é só pedir."
        return resposta

    proximo   = proximo_campo_vazio(sid)
    resposta += f"\n💬 {PERGUNTAS[proximo]}"
    return resposta


def gerar_resposta(mensagem_usuario, sid=None):
    tokens, lemas   = preprocessar(mensagem_usuario)
    intencao        = detectar_intencao(mensagem_usuario)
    genero_afirmado, genero_negado = detectar_genero(tokens, lemas, texto_bruto=mensagem_usuario)
    tipo_ref, nome_ref = _detectar_referencia_texto(mensagem_usuario)
    pais = detectar_pais(mensagem_usuario)

    print(f"[DEBUG] tokens={tokens} | genero={genero_afirmado}/{genero_negado} | intencao={intencao} | ref={tipo_ref}:{nome_ref} | pais={pais} | sid={sid}")

    if genero_negado and sid:
        banir_genero(sid, genero_negado)

    if intencao == "mais_filmes" and sid:
        ref = get_referencia(sid)
        if ref:
            return _montar_resposta_por_entidade(sid), sid
        return _montar_resposta_filmes(sid), sid

    if intencao == "saudacao":
        return (
            "Olá! 🎬 Sou o CineBot, seu assistente de filmes!\n\n"
            "Me diz que gênero você quer assistir:\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense\n\n"
            "💡 Você também pode dizer:\n"
            "• \"Algo como Inception\"\n"
            "• \"Filmes com Tom Holland\"\n"
            "• \"Quero ação com o Brad Pitt\""
        ), sid

    if intencao == "despedida":
        if sid:
            encerrar_sessao(sid)
            sid = None
        return "Foi um prazer! Bom filme e até mais! 👋", sid

    if intencao == "ajuda":
        return (
            "É simples! Me diga o gênero que você quer. Por exemplo:\n\n"
            "• \"Quero ação\"\n"
            "• \"Me indica uma comédia\"\n"
            "• \"Sugere um suspense\"\n\n"
            "Ou use referências:\n"
            "• \"Algo como Inception\" → filmes similares\n"
            "• \"Filmes com Tom Holland\" → filmografia do ator\n"
            "• \"Filmes do diretor Christopher Nolan\" → filmografia do diretor\n"
            "• \"Quero ação com o Brad Pitt\" → gênero + pessoa\n\n"
            "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        ), sid

    if sid and genero_afirmado:
        proximo = proximo_campo_vazio(sid)
        if proximo and proximo != "genero_pedido":
            valor = _detectar_valor_campo(proximo, tokens, lemas)
            if valor:
                genero_afirmado = None

    if genero_afirmado:
        sessao       = obter_sessao(sid) if sid else None
        genero_atual = sessao.get("genero_pedido") if sessao else None

        if sid and genero_afirmado == genero_atual:
            if _tem_enfase_no_genero(mensagem_usuario, genero_afirmado):
                travar_genero(sid)
                nome = NOMES_GENEROS[genero_afirmado]
                return (
                    f"Entendido! Vou te recomendar apenas **{nome}** daqui pra frente. 🎬\n\n"
                    + _montar_resposta_filmes(sid)
                ), sid
            return _montar_resposta_filmes(sid), sid

        if sid:
            encerrar_sessao(sid)
        sid = criar_sessao()
        preencher_campo(sid, "genero_pedido", genero_afirmado)
        if pais:
            set_pais(sid, pais)

        candidato_ator = nome_ref if tipo_ref == "ator" else _detectar_ator_em_mensagem_com_genero(mensagem_usuario)
        if candidato_ator:
            entidade = identificar_entidade(candidato_ator, tipo_hint="ator")
            if entidade:
                set_referencia(sid, "ator", entidade["id"], entidade["nome"])
                return _montar_resposta_por_entidade(sid), sid

        return _montar_resposta_filmes(sid), sid

    if genero_negado and not sid:
        return (
            f"Entendido, sem **{NOMES_GENEROS.get(genero_negado, genero_negado)}**! 😊 "
            f"Que tal tentar outro gênero?\n\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense"
        ), sid

    if pais and not genero_afirmado:
        if sid:
            encerrar_sessao(sid)
        sid = criar_sessao()
        set_pais(sid, pais)
        return _montar_resposta_filmes(sid), sid

    if sid:
        ref = get_referencia(sid)

        if ref and not genero_afirmado and not tipo_ref:
            if intencao in ("mais_filmes", "recomendacao"):
                return _montar_resposta_por_entidade(sid), sid

        if tipo_ref and nome_ref:
            entidade = identificar_entidade(nome_ref, tipo_hint=tipo_ref)
            if entidade:
                encerrar_sessao(sid)
                sid = criar_sessao()
                set_referencia(sid, entidade["tipo"], entidade["id"], entidade["nome"])
                if entidade["tipo"] == "filme" and entidade.get("generos"):
                    preencher_campo(sid, "genero_pedido", entidade["generos"][0])
                return _montar_resposta_por_entidade(sid), sid

        proximo = proximo_campo_vazio(sid)
        if proximo:
            valor = _detectar_valor_campo(proximo, tokens, lemas)
            if valor:
                preencher_campo(sid, proximo, valor)
                if deve_recomendar(sid):
                    return _montar_resposta_filmes(sid), sid
                novo_proximo = proximo_campo_vazio(sid)
                return f"Anotado! 😊 {PERGUNTAS[novo_proximo]}", sid
            return f"Não entendi bem. 😅 {PERGUNTAS[proximo]}", sid

    if tipo_ref and nome_ref:
        entidade = identificar_entidade(nome_ref, tipo_hint=tipo_ref)
        if entidade:
            sid = criar_sessao()
            set_referencia(sid, entidade["tipo"], entidade["id"], entidade["nome"])
            if entidade["tipo"] == "filme" and entidade.get("generos"):
                preencher_campo(sid, "genero_pedido", entidade["generos"][0])
            return _montar_resposta_por_entidade(sid), sid
        return (
            f"Não encontrei **\"{nome_ref}\"** no TMDB. 🤔\n"
            "Tente um nome diferente, ou me diga um gênero!"
        ), sid

    if intencao == "recomendacao":
        return (
            "Qual gênero você quer? 🎬\n"
            "Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação ou Suspense.\n\n"
            "💡 Ou tente:\n"
            "• \"Algo como Inception\"\n"
            "• \"Filmes com Tom Holland\"\n"
            "• \"Quero ação com o Brad Pitt\""
        ), sid

    return (
        "Não entendi muito bem... 😅 Tente me dizer o gênero do filme que você quer!\n\n"
        "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação, Suspense.\n\n"
        "💡 Ou tente:\n"
        "• \"Algo como Inception\"\n"
        "• \"Filmes com Tom Holland\""
    ), sid
