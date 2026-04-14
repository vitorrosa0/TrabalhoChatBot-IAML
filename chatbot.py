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
from tmdb_api import buscar_filmes_por_genero
from session_manager import (
    criar_sessao, obter_sessao, preencher_campo,
    deve_recomendar, proximo_campo_vazio, sessao_completa,
    encerrar_sessao, adicionar_filmes_recomendados,
    filmes_ja_recomendados, campos_preenchidos, PERGUNTAS,
    banir_genero, generos_banidos, travar_genero,
    genero_esta_travado, destravar_genero,
    set_genero_recomendado, get_genero_recomendado,
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
    "acao": "Ação", "comedia": "Comédia", "drama": "Drama",
    "terror": "Terror", "romance": "Romance",
    "ficcao_cientifica": "Ficção Científica",
    "animacao": "Animação", "suspense": "Suspense",
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
    """
    Detecta gêneros na mensagem separando os negados dos afirmados.
    Retorna (genero_afirmado, genero_negado).
    """
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
                break  # encontrou esse gênero, passa para o próximo

    return genero_afirmado, genero_negado

def _tem_enfase_no_genero(texto_bruto, genero_pedido):
    """
    Detecta se o usuário está enfatizando o gênero que pediu.
    Ex: 'só quero ação', 'apenas ação', 'quero apenas animação'
    Verifica palavras individuais restritivas e bigrams.
    """
    tokens_brutos = word_tokenize(texto_bruto.lower(), language="portuguese")
    lemas_genero  = LEMAS_GENEROS.get(genero_pedido, [])

    tem_genero_pedido = any(
        lematizar(t) in lemas_genero or t in MAPA_GENEROS.get(genero_pedido, [])
        for t in tokens_brutos
    )
    if not tem_genero_pedido:
        return False

    # Palavras restritivas individuais
    ENFASE_SIMPLES = {"só", "so", "apenas", "somente", "prefiro", "insisto"}
    tem_enfase = any(p in tokens_brutos for p in ENFASE_SIMPLES)

    # Bigrams restritivos: "quero apenas", "só quero", "quero só"
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

def _montar_resposta_filmes(sid):
    sessao = obter_sessao(sid)

    genero_pedido = sessao.get("genero_pedido")
    humor         = sessao.get("humor") or "calmo"
    acompanhado   = sessao.get("acompanhado") or "sozinho"
    duracao       = sessao.get("duracao_preferida") or "medio"
    disposicao    = sessao.get("disposicao") or "curtir"
    banidos       = generos_banidos(sid)
    travado       = genero_esta_travado(sid)

    if travado:
        # Usuário insistiu no gênero pedido — ignora o ML
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

        # Se o ML sugeriu um gênero banido, cai no genero_pedido
        if genero_final in banidos:
            print(f"[Banido] ML sugeriu '{genero_final}' que está banido. Usando '{genero_pedido}'.")
            genero_final = genero_pedido
            nota_ml = (
                f"🤖 _O ML sugeriu um gênero que você não quer. "
                f"Usando **{NOMES_GENEROS[genero_final]}** no lugar._\n\n"
            )

    ja_vistos = filmes_ja_recomendados(sid)
    # Salva o gênero que foi de fato recomendado na sessão
    set_genero_recomendado(sid, genero_final)
    filmes = buscar_filmes_por_genero(
        genero_final,
        quantidade=3,
        excluir_titulos=ja_vistos,
        duracao=sessao.get("duracao_preferida"),
    )
    adicionar_filmes_recomendados(sid, [f["titulo"] for f in filmes])

    nome_genero = NOMES_GENEROS.get(genero_final, genero_final)
    resposta    = f"🎬 Aqui estão filmes de **{nome_genero}** pra você:\n\n"

    for i, filme in enumerate(filmes, 1):
        estrelas     = f" ⭐ {filme['nota']}/10" if filme.get("nota") else ""
        duracao_min  = filme.get("duracao_min")
        info_duracao = f" ⏱ {duracao_min} min" if duracao_min else ""
        resposta    += f"{i}. **{filme['titulo']}** ({filme['ano']}){estrelas}{info_duracao}\n"
        resposta    += f"   _{filme['descricao']}_\n\n"

    resposta += nota_ml

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

    print(f"[DEBUG] tokens={tokens} | genero_afirmado={genero_afirmado} | genero_negado={genero_negado} | intencao={intencao} | sid={sid}")

    if genero_negado and sid:
        banir_genero(sid, genero_negado)

    if intencao == "mais_filmes" and sid:
        return _montar_resposta_filmes(sid), sid

    if intencao == "saudacao":
        return (
            "Olá! 🎬 Sou o CineBot, seu assistente de filmes!\n\n"
            "Me diz que gênero você quer assistir:\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense"
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
            "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        ), sid

    if genero_afirmado:
        sessao = obter_sessao(sid) if sid else None
        genero_atual = sessao.get("genero_pedido") if sessao else None

        if sid and genero_afirmado == genero_atual:
            # Mesmo gênero que o usuário pediu originalmente — mantém sessão
            if _tem_enfase_no_genero(mensagem_usuario, genero_afirmado):
                # Usuário insistiu ("só quero animação") — trava o ML
                travar_genero(sid)
                nome = NOMES_GENEROS[genero_afirmado]
                return (
                    f"Entendido! Vou te recomendar apenas **{nome}** daqui pra frente. 🎬\n\n"
                    + _montar_resposta_filmes(sid)
                ), sid
            else:
                return _montar_resposta_filmes(sid), sid

        if sid:
            encerrar_sessao(sid)
        sid = criar_sessao()
        preencher_campo(sid, "genero_pedido", genero_afirmado)
        return _montar_resposta_filmes(sid), sid

    if genero_negado:
        return (
            f"Entendido, sem **{NOMES_GENEROS.get(genero_negado, genero_negado)}**! 😊 "
            f"Que tal tentar outro gênero?\n\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense"
        ), sid

    if sid:
        proximo = proximo_campo_vazio(sid)
        if proximo:
            valor = _detectar_valor_campo(proximo, tokens, lemas)
            if valor:
                preencher_campo(sid, proximo, valor)
                if deve_recomendar(sid):
                    return _montar_resposta_filmes(sid), sid
                else:
                    novo_proximo = proximo_campo_vazio(sid)
                    return f"Anotado! 😊 {PERGUNTAS[novo_proximo]}", sid
            else:
                return f"Não entendi bem. 😅 {PERGUNTAS[proximo]}", sid

    if intencao == "recomendacao":
        return (
            "Qual gênero você quer? 🎬\n"
            "Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação ou Suspense."
        ), sid

    return (
        "Não entendi muito bem... 😅 Tente me dizer o gênero do filme que você quer!\n\n"
        "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação, Suspense."
    ), sid