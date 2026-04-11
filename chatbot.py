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
)

STOPWORDS_PT = set(stopwords.words("portuguese"))

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
    "familia": [lematizar(p) for p in ["familia","filho","filha","pai","mae","crianca","filhos"]],
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

def detectar_genero(tokens, lemas):
    for genero, lemas_genero in LEMAS_GENEROS.items():
        for lema in lemas:
            if lema in lemas_genero:
                return genero
        for token in tokens:
            if token in MAPA_GENEROS[genero]:
                return genero
    return None

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

    genero_pedido    = sessao.get("genero_pedido")
    humor            = sessao.get("humor") or "calmo"
    acompanhado      = sessao.get("acompanhado") or "sozinho"
    duracao          = sessao.get("duracao_preferida") or "medio"
    disposicao       = sessao.get("disposicao") or "curtir"

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

    ja_vistos = filmes_ja_recomendados(sid)
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
        estrelas  = f" ⭐ {filme['nota']}/10" if filme.get("nota") else ""
        resposta += f"{i}. **{filme['titulo']}** ({filme['ano']}){estrelas}\n"
        resposta += f"   _{filme['descricao']}_\n\n"

    resposta += nota_ml

    if sessao_completa(sid):
        salvar_exemplo(genero_pedido, humor, acompanhado, duracao, disposicao, genero_final)
        encerrar_sessao(sid)
        resposta += "Espero que curta! 🍿 Se quiser mais recomendações, é só pedir."
        return resposta

    proximo   = proximo_campo_vazio(sid)
    resposta += f"💬 {PERGUNTAS[proximo]}"
    return resposta


def gerar_resposta(mensagem_usuario, sid=None):
    tokens, lemas = preprocessar(mensagem_usuario)
    intencao      = detectar_intencao(mensagem_usuario)
    genero        = detectar_genero(tokens, lemas)

    print(f"[DEBUG] tokens={tokens} | lemas={lemas} | genero={genero} | intencao={intencao} | sid={sid}")

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

    if genero:
        if sid:
            encerrar_sessao(sid)
        sid = criar_sessao()
        preencher_campo(sid, "genero_pedido", genero)
        return _montar_resposta_filmes(sid), sid

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