"""
nlp_engine/intent_classifier.py
Classificador de intenções usando NLTK + Scikit-Learn (CountVectorizer + MultinomialNB).
"""
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np

for resource in ["stopwords", "rslp", "punkt", "punkt_tab"]:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass


class IntentClassifier:
    TRAINING_DATA = [
        # saudacao
        ("oi", "saudacao"),
        ("olá", "saudacao"),
        ("boa tarde", "saudacao"),
        ("bom dia", "saudacao"),
        ("boa noite", "saudacao"),
        ("hey", "saudacao"),
        ("e aí", "saudacao"),
        ("tudo bem", "saudacao"),
        ("oi tudo bem", "saudacao"),
        ("olá como vai", "saudacao"),
        ("salve", "saudacao"),
        ("oi bot", "saudacao"),

        # despedida
        ("tchau", "despedida"),
        ("até logo", "despedida"),
        ("até mais", "despedida"),
        ("valeu tchau", "despedida"),
        ("obrigado até mais", "despedida"),
        ("flw", "despedida"),
        ("falou", "despedida"),
        ("encerrando aqui", "despedida"),

        # recomendar_filme
        ("me indica um filme", "recomendar_filme"),
        ("quero ver um filme", "recomendar_filme"),
        ("tem alguma recomendação", "recomendar_filme"),
        ("o que vale a pena assistir", "recomendar_filme"),
        ("me sugere algo para assistir", "recomendar_filme"),
        ("qual filme você recomenda", "recomendar_filme"),
        ("me recomenda um filme", "recomendar_filme"),
        ("quero indicação de filme", "recomendar_filme"),
        ("me indica algo bom", "recomendar_filme"),
        ("que filme assistir hoje", "recomendar_filme"),
        ("quero assistir algo novo", "recomendar_filme"),
        ("me recomenda um filme de ação", "recomendar_filme"),
        ("quero ver um drama", "recomendar_filme"),
        ("me sugere uma comédia", "recomendar_filme"),
        ("filmes brasileiros bons", "recomendar_filme"),
        ("algum filme coreano", "recomendar_filme"),
        ("me indica filme nacional", "recomendar_filme"),
        ("recomenda algo do nolan", "recomendar_filme"),
        ("tem filme do tarantino", "recomendar_filme"),
        ("quero ver algo japonês", "recomendar_filme"),
        ("me indica um terror", "recomendar_filme"),
        ("sugere um filme de aventura", "recomendar_filme"),
        ("boa indicação de ficção científica", "recomendar_filme"),

        # buscar_diretor
        ("quem dirige esse filme", "buscar_diretor"),
        ("quem é o diretor", "buscar_diretor"),
        ("quem dirigiu", "buscar_diretor"),
        ("me fala do diretor", "buscar_diretor"),
        ("qual o diretor do filme", "buscar_diretor"),
        ("quem é fernando meirelles", "buscar_diretor"),
        ("me conta sobre o tarantino", "buscar_diretor"),
        ("filmes do christopher nolan", "buscar_diretor"),
        ("o nolan fez quais filmes", "buscar_diretor"),
        ("obras do kubrick", "buscar_diretor"),
        ("quais diretores estão no catálogo", "buscar_diretor"),
        ("diretores populares", "buscar_diretor"),
        ("me fala sobre o spielberg", "buscar_diretor"),

        # buscar_filme
        ("fala sobre cidade de deus", "buscar_filme"),
        ("o que é pulp fiction", "buscar_filme"),
        ("me conta sobre matrix", "buscar_filme"),
        ("o que você sabe sobre parasita", "buscar_filme"),
        ("me fale do filme clube da luta", "buscar_filme"),
        ("conta a sinopse de interestelar", "buscar_filme"),
        ("de que se trata vingadores", "buscar_filme"),
        ("me fala de homem aranha", "buscar_filme"),
        ("o que é o auto da compadecida", "buscar_filme"),
        ("sinopse do filme", "buscar_filme"),
        ("me conta sobre esse filme", "buscar_filme"),

        # sobre_genero
        ("me fala de filmes de terror", "sobre_genero"),
        ("gosto de drama", "sobre_genero"),
        ("prefiro comédia", "sobre_genero"),
        ("ação é meu favorito", "sobre_genero"),
        ("gosto de thriller", "sobre_genero"),
        ("ficção científica tem algum bom", "sobre_genero"),
        ("que gêneros você conhece", "sobre_genero"),
        ("crime me interessa", "sobre_genero"),
        ("gosto de suspense", "sobre_genero"),
        ("tem animação", "sobre_genero"),
        ("quero ver aventura", "sobre_genero"),
        ("filmes de fantasia", "sobre_genero"),

        # sobre_pais
        ("tem filme brasileiro", "sobre_pais"),
        ("quero algo nacional", "sobre_pais"),
        ("filmes americanos bons", "sobre_pais"),
        ("cinema coreano é top", "sobre_pais"),
        ("o que tem de francês", "sobre_pais"),
        ("cinema brasileiro", "sobre_pais"),
        ("produções nacionais", "sobre_pais"),
        ("algum filme da coreia", "sobre_pais"),
        ("cinema japonês", "sobre_pais"),
        ("filme mexicano", "sobre_pais"),
        ("produções indianas", "sobre_pais"),
        ("cinema argentino", "sobre_pais"),

        # avaliacao
        ("qual filme tem nota maior", "avaliacao"),
        ("o melhor filme da lista", "avaliacao"),
        ("qual tem melhor avaliação", "avaliacao"),
        ("o mais bem avaliado", "avaliacao"),
        ("qual tem o maior rating", "avaliacao"),
        ("nota do filme", "avaliacao"),
        ("qual vale mais a pena", "avaliacao"),
        ("melhores filmes do catálogo", "avaliacao"),
        ("top filmes", "avaliacao"),

        # curiosidade
        ("me conta uma curiosidade", "curiosidade"),
        ("algo interessante sobre filmes", "curiosidade"),
        ("fact sobre cinema", "curiosidade"),
        ("me surpreende", "curiosidade"),
        ("alguma coisa aleatória sobre cinema", "curiosidade"),
        ("fato curioso", "curiosidade"),
        ("você sabia", "curiosidade"),
        ("me conta algo legal", "curiosidade"),

        # outro
        ("qual seu nome", "outro"),
        ("você é um bot", "outro"),
        ("quem te criou", "outro"),
        ("o que você faz", "outro"),
        ("como você funciona", "outro"),
        ("me ajuda", "outro"),
    ]

    def __init__(self):
        self._stemmer = RSLPStemmer()
        try:
            self._stopwords = set(stopwords.words("portuguese"))
        except Exception:
            self._stopwords = set()
        self._pipeline = self._build_pipeline()
        self._train()

    def _preprocess(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-záéíóúâêîôûãõç\s]", " ", text)
        tokens = text.split()
        tokens = [t for t in tokens if t not in self._stopwords]
        tokens = [self._stemmer.stem(t) for t in tokens]
        return " ".join(tokens)

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("vectorizer", CountVectorizer(
                preprocessor=self._preprocess,
                ngram_range=(1, 2),
                min_df=1,
            )),
            ("classifier", MultinomialNB(alpha=0.5)),
        ])

    def _train(self):
        texts  = [t for t, _ in self.TRAINING_DATA]
        labels = [l for _, l in self.TRAINING_DATA]
        self._pipeline.fit(texts, labels)

    def predict(self, text: str) -> str:
        return self._pipeline.predict([text])[0]

    def predict_proba(self, text: str) -> dict:
        classes = self._pipeline.classes_
        probs   = self._pipeline.predict_proba([text])[0]
        return dict(zip(classes, probs))

    def confidence(self, text: str) -> float:
        probs = self._pipeline.predict_proba([text])[0]
        return float(np.max(probs))