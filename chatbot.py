import nltk
import random
import string
import simplemma
from filmes import FILMES, MAPA_GENEROS
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Inicializa as stopwords em português
STOPWORDS_PT = set(stopwords.words("portuguese"))


def lematizar(palavra):
    return simplemma.lemmatize(palavra, lang="pt")


# Lemas pré-computados para comparação
LEMAS_GENEROS = {}
for genero, palavras in MAPA_GENEROS.items():
    LEMAS_GENEROS[genero] = [lematizar(p) for p in palavras]

FRASES_TREINO = [
    "oi", "olá", "ola", "hey",
    "bom", "boa", "salve",
    "opa", "eai", "tudo bem",

    "tchau", "ate", "até", "adeus",
    "obrigado", "valeu", "sair",
    "encerrar", "obrigada",

    "como", "o que", "fazer", "funcionar",
    "usar", "ajudar", "help",
    "que", "quais", "dizer", "explicar",

    "querer", "recomendar",
    "sugerir", "indicar", "mostrar",
    "tem algum filme bom", "precisar",
    "ver", "passar", "assistir",
]

ROTULOS_TREINO = [
    "saudacao", "saudacao", "saudacao", "saudacao",
    "saudacao", "saudacao", "saudacao",
    "saudacao", "saudacao", "saudacao",

    "despedida", "despedida", "despedida", "despedida",
    "despedida", "despedida", "despedida",
    "despedida", "despedida",

    "ajuda", "ajuda", "ajuda", "ajuda",
    "ajuda", "ajuda", "ajuda",
    "ajuda", "ajuda", "ajuda", "ajuda",

    "recomendacao", "recomendacao",
    "recomendacao", "recomendacao", "recomendacao",
    "recomendacao", "recomendacao",
    "recomendacao", "recomendacao", "recomendacao",
]

assert len(FRASES_TREINO) == len(ROTULOS_TREINO), (
    f"Desalinhamento: {len(FRASES_TREINO)} frases vs {len(ROTULOS_TREINO)} rótulos"
)


def _preprocessar_treino(texto):
    """Pré-processamento usado só no treino do modelo."""
    texto = texto.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    return " ".join([lematizar(t) for t in tokens])

_frases_proc = [_preprocessar_treino(f) for f in FRASES_TREINO]

_vectorizer = CountVectorizer()
_X_treino   = _vectorizer.fit_transform(_frases_proc)

_modelo_intencao = MultinomialNB()
_modelo_intencao.fit(_X_treino, ROTULOS_TREINO)


def preprocessar(texto):
    """
    Aplica pipeline de PLN:
    1. Lowercase
    2. Remove pontuação
    3. Tokenização
    4. Remoção de stopwords
    5. Lematização (simplemma)
    """
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


def detectar_intencao(tokens, lemas):
    """Classifica a intenção usando MultinomialNB."""
    entrada = " ".join(lemas)
    vetor   = _vectorizer.transform([entrada])
    return _modelo_intencao.predict(vetor)[0]


def recomendar_filmes(genero, quantidade=3):
    filmes = FILMES.get(genero, [])
    selecionados = random.sample(filmes, min(quantidade, len(filmes)))
    return selecionados


def gerar_resposta(mensagem_usuario):
    tokens, lemas = preprocessar(mensagem_usuario)
    intencao = detectar_intencao(tokens, lemas)
    genero = detectar_genero(tokens, lemas)

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
        filmes = recomendar_filmes(genero)
        nomes_generos = {
            "acao": "Ação", "comedia": "Comédia", "drama": "Drama",
            "terror": "Terror", "romance": "Romance",
            "ficcao_cientifica": "Ficção Científica",
            "animacao": "Animação", "suspense": "Suspense",
        }
        nome_genero = nomes_generos.get(genero, genero)
        resposta = f"🎬 Ótima escolha! Aqui estão {len(filmes)} filmes de **{nome_genero}** pra você:\n\n"
        for i, filme in enumerate(filmes, 1):
            resposta += f"{i}. **{filme['titulo']}** ({filme['ano']})\n"
            resposta += f"   _{filme['descricao']}_\n\n"
        resposta += "Quer recomendações de outro gênero? 😊"
        return resposta

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