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

STOPWORDS_PT = set(stopwords.words("portuguese"))

def lematizar(palavra: str) -> str:
    return simplemma.lemmatize(palavra, lang="pt")

def preprocessar(texto: str):
    texto  = texto.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(texto, language="portuguese")
    tokens = [t for t in tokens if t not in STOPWORDS_PT]
    lemas  = [lematizar(t) for t in tokens]
    return tokens, lemas

def _extrair_features(texto: str) -> dict:
    tokens, lemas = preprocessar(texto)
    return {f"lema_{l}": True for l in lemas}

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

_dados_formatados      = [(_extrair_features(f), i) for f, i in DADOS_TREINO_BRUTOS]
classificador_intencao = NaiveBayesClassifier.train(_dados_formatados)
_acuracia              = accuracy(classificador_intencao, _dados_formatados)
print(f"[NaiveBayes] Classificador treinado. Acurácia: {_acuracia:.1%}")

def detectar_intencao(texto_original: str) -> str:
    features = _extrair_features(texto_original)
    if not features:
        return "desconhecida"
    intencao = classificador_intencao.classify(features)
    prob     = classificador_intencao.prob_classify(features).prob(intencao)
    print(f"[NaiveBayes] Intenção: '{intencao}' (confiança: {prob:.1%})")
    return intencao if prob >= 0.35 else "desconhecida"