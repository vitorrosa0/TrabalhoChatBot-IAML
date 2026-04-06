import nltk
import random
import string
import simplemma
from datetime import datetime
from filmes import FILMES, MAPA_GENEROS
from ml_recomendador import recomendar_com_ambos, salvar_exemplo, MINIMO_TREINO
from tmdb_api import buscar_nota_filme

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.classify import NaiveBayesClassifier
from nltk.classify.util import accuracy

STOPWORDS_PT = set(stopwords.words("portuguese"))


def lematizar(palavra):
    return simplemma.lemmatize(palavra, lang="pt")


DADOS_TREINO_BRUTOS = [
    # saudacao
    ("oi", "saudacao"),
    ("olá", "saudacao"),
    ("ola", "saudacao"),
    ("oi tudo bem", "saudacao"),
    ("hey", "saudacao"),
    ("bom dia", "saudacao"),
    ("boa tarde", "saudacao"),
    ("boa noite", "saudacao"),
    ("salve", "saudacao"),
    ("opa", "saudacao"),
    ("e aí", "saudacao"),
    ("e ai tudo certo", "saudacao"),
    ("olá como vai", "saudacao"),
    ("oi boa tarde", "saudacao"),
    ("hey tudo bem", "saudacao"),
    ("salve salve", "saudacao"),
    ("boas", "saudacao"),
    ("oi sumido", "saudacao"),

    # despedida
    ("tchau", "despedida"),
    ("até mais", "despedida"),
    ("adeus", "despedida"),
    ("valeu", "despedida"),
    ("obrigado", "despedida"),
    ("obrigada", "despedida"),
    ("até logo", "despedida"),
    ("foi bom falar", "despedida"),
    ("encerrando", "despedida"),
    ("quero sair", "despedida"),
    ("vou encerrar", "despedida"),
    ("até amanhã", "despedida"),
    ("muito obrigado pela ajuda", "despedida"),
    ("valeu mesmo", "despedida"),
    ("flw", "despedida"),
    ("até", "despedida"),
    ("encerrar conversa", "despedida"),

    # ajuda
    ("como funciona", "ajuda"),
    ("como usar", "ajuda"),
    ("me ajuda", "ajuda"),
    ("o que você faz", "ajuda"),
    ("o que você pode fazer", "ajuda"),
    ("preciso de ajuda", "ajuda"),
    ("help", "ajuda"),
    ("como faço para", "ajuda"),
    ("não sei como usar", "ajuda"),
    ("pode me explicar", "ajuda"),
    ("quais são as opções", "ajuda"),
    ("o que posso pedir", "ajuda"),
    ("como funciona isso", "ajuda"),
    ("me explica", "ajuda"),
    ("tem tutorial", "ajuda"),
    ("instruções", "ajuda"),

    # recomendacao
    ("quero um filme", "recomendacao"),
    ("me recomenda um filme", "recomendacao"),
    ("sugere algum filme", "recomendacao"),
    ("indica um filme", "recomendacao"),
    ("quero assistir algo", "recomendacao"),
    ("me mostra um filme", "recomendacao"),
    ("quero ver um filme", "recomendacao"),
    ("me sugere algo", "recomendacao"),
    ("qual filme devo assistir", "recomendacao"),
    ("tem algum filme bom", "recomendacao"),
    ("me indica algo para ver hoje", "recomendacao"),
    ("quero uma recomendação", "recomendacao"),
    ("o que assistir", "recomendacao"),
    ("me dá uma dica de filme", "recomendacao"),
    ("que filme você recomenda", "recomendacao"),
    ("preciso de indicação de filme", "recomendacao"),
]


def _extrair_features(texto):
    texto = texto.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    lemas = [lematizar(t) for t in tokens]
    return {f"lema_{lema}": True for lema in lemas}


def _preparar_dados_treino(dados_brutos):
    return [(_extrair_features(frase), intencao)
            for frase, intencao in dados_brutos]



_dados_formatados = _preparar_dados_treino(DADOS_TREINO_BRUTOS)
classificador_intencao = NaiveBayesClassifier.train(_dados_formatados)

_acuracia = accuracy(classificador_intencao, _dados_formatados)
print(f"[NaiveBayes] Classificador treinado. Acurácia no treino: {_acuracia:.1%}")

LEMAS_GENEROS = {}
for genero, palavras in MAPA_GENEROS.items():
    LEMAS_GENEROS[genero] = [lematizar(p) for p in palavras]

LEMAS_HUMOR = {
    "animado":   [lematizar(p) for p in ["animado", "empolgado", "energia", "agitado", "feliz"]],
    "calmo":     [lematizar(p) for p in ["calmo", "relaxado", "tranquilo", "sossegado", "descansando"]],
    "entediado": [lematizar(p) for p in ["entediado", "tedio", "chato", "sem", "fazer"]],
    "assustado": [lematizar(p) for p in ["assustado", "medo", "nervoso", "tenso", "ansioso"]],
    "romantico": [lematizar(p) for p in ["romantico", "apaixonado", "amor", "namorado", "namorada"]],
    "curioso":   [lematizar(p) for p in ["curioso", "pensativo", "refletindo", "interessado", "intrigado"]],
}

LEMAS_ACOMPANHADO = {
    "sozinho": [lematizar(p) for p in ["sozinho", "solo", "so"]],
    "amigos":  [lematizar(p) for p in ["amigos", "amigo", "galera", "turma", "pessoal"]],
    "casal":   [lematizar(p) for p in ["casal", "namorado", "namorada", "esposo", "esposa", "parceiro", "parceira"]],
    "familia": [lematizar(p) for p in ["familia", "filho", "filha", "pai", "mae", "crianca"]],
}

NOMES_GENEROS = {
    "acao": "Ação", "comedia": "Comédia", "drama": "Drama",
    "terror": "Terror", "romance": "Romance",
    "ficcao_cientifica": "Ficção Científica",
    "animacao": "Animação", "suspense": "Suspense",
}


def preprocessar(texto):
    texto = texto.lower()
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    lemas = [lematizar(t) for t in tokens]
    return tokens, lemas


def detectar_genero(tokens, lemas):
    for genero, lemas_genero in LEMAS_GENEROS.items():
        for lema_input in lemas:
            if lema_input in lemas_genero:
                return genero
        for token in tokens:
            if token in MAPA_GENEROS[genero]:
                return genero
    return None


def detectar_intencao(texto_original):
    features = _extrair_features(texto_original)

    if not features:
        return "desconhecida"

    intencao = classificador_intencao.classify(features)

    dist = classificador_intencao.prob_classify(features)
    prob = dist.prob(intencao)
    print(f"[NaiveBayes] Intenção: '{intencao}' (confiança: {prob:.1%})")

    if prob < 0.35:
        return "desconhecida"

    return intencao


def detectar_humor(lemas):
    for humor, lemas_humor in LEMAS_HUMOR.items():
        for lema in lemas:
            if lema in lemas_humor:
                return humor
    return "calmo"


def detectar_acompanhado(lemas):
    for comp, lemas_comp in LEMAS_ACOMPANHADO.items():
        for lema in lemas:
            if lema in lemas_comp:
                return comp
    return "sozinho"


def detectar_idade(tokens):
    for token in tokens:
        if token in ["jovem", "novo", "nova", "adolescente", "teen"]:
            return "jovem"
        if token in ["idoso", "velho", "velha", "aposentado", "senior"]:
            return "idoso"
    return "adulto"


def detectar_hora():
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "manha"
    elif 12 <= hora < 18:
        return "tarde"
    else:
        return "noite"


def detectar_dia():
    return "fim_semana" if datetime.now().weekday() >= 5 else "semana"


def recomendar_filmes(genero, quantidade=3):
    filmes = FILMES.get(genero, [])
    return random.sample(filmes, min(quantidade, len(filmes)))


def _resposta_com_ml(genero_detectado, lemas, tokens):
    humor       = detectar_humor(lemas)
    acompanhado = detectar_acompanhado(lemas)
    idade       = detectar_idade(tokens)
    hora        = detectar_hora()
    dia         = detectar_dia()

    genero_j48, genero_lmt = recomendar_com_ambos(
        idade, genero_detectado, hora, dia, humor, acompanhado
    )

    if genero_j48 is None:
        genero_final = genero_detectado
        nota_ml = f"🤖 _Ainda aprendendo... usando o gênero que você pediu. ({MINIMO_TREINO} interações necessárias para ativar o ML)_\n\n"
    elif genero_j48 == genero_lmt:
        genero_final = genero_j48
        nota_ml = f"🤖 _J48 e LMT concordaram: **{NOMES_GENEROS[genero_final]}** é o melhor para o seu perfil agora._\n\n"
    else:
        genero_final = genero_j48
        nota_ml = (
            f"🤖 _J48 indicou **{NOMES_GENEROS[genero_j48]}** e "
            f"LMT indicou **{NOMES_GENEROS[genero_lmt]}**. "
            f"Usando J48 (maior acurácia no experimento)._\n\n"
        )

    salvar_exemplo(idade, genero_detectado, hora, dia, humor, acompanhado, genero_final)

    filmes = recomendar_filmes(genero_final)
    nome_genero = NOMES_GENEROS.get(genero_final, genero_final)

    resposta = f"🎬 Ótima escolha! Aqui estão {len(filmes)} filmes de **{nome_genero}** pra você:\n\n"
    for i, filme in enumerate(filmes, 1):
        nota = buscar_nota_filme(filme["titulo"])
        estrelas = f" ⭐ {nota}/10" if nota else ""
        print(f"[TMDB] '{filme['titulo']}' → nota: {nota}")
        resposta += f"{i}. **{filme['titulo']}** ({filme['ano']}){estrelas}\n"
        resposta += f"   _{filme['descricao']}_\n\n"
    resposta += nota_ml
    resposta += "Quer recomendações de outro gênero? 😊"
    return resposta


def gerar_resposta(mensagem_usuario):
    tokens, lemas = preprocessar(mensagem_usuario)
    intencao = detectar_intencao(mensagem_usuario)  # passa o texto original
    genero   = detectar_genero(tokens, lemas)

    print(f"tokens: {tokens}")
    print(f"lemas:  {lemas}")
    print(f"genero detectado: {genero}")
    print(f"intencao: {intencao}")

    if intencao == "saudacao":
        return (
            "Olá! 🎬 Sou o CineBot, seu assistente de recomendação de filmes!\n\n"
            "Posso te recomendar filmes de vários gêneros:\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense\n\n"
            "É só me dizer o que você quer assistir!"
        )

    if intencao == "despedida":
        return "Foi um prazer recomendar filmes pra você! 🎬 Bom filme e até mais! 👋"

    if intencao == "ajuda":
        return (
            "É simples! Me diga o tipo de filme que você quer assistir. Por exemplo:\n\n"
            "• \"Quero um filme de ação\"\n"
            "• \"Me recomenda uma comédia\"\n"
            "• \"Estou com medo, quero terror\"\n"
            "• \"Algo romântico para hoje à noite\"\n\n"
            "Gêneros disponíveis: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        )

    if genero:
        return _resposta_com_ml(genero, lemas, tokens)

    if intencao == "recomendacao":
        return (
            "Hmm, não identifiquei o gênero que você quer! 🤔\n\n"
            "Tente me dizer algo como:\n"
            "• \"Quero ação\"\n"
            "• \"Me indica uma comédia\"\n"
            "• \"Sugere um suspense\"\n\n"
            "Gêneros disponíveis: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        )

    return (
        "Não entendi muito bem... 😅 Mas posso te recomendar filmes!\n\n"
        "Tente dizer algo como:\n"
        "• \"Quero um filme de ação\"\n"
        "• \"Me recomenda uma comédia\"\n"
        "• \"Sugere ficção científica\"\n\n"
        "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação, Suspense."
    )