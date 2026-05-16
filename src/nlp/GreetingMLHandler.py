import unicodedata
from typing import List

from nltk.stem import RSLPStemmer
from nltk.classify import NaiveBayesClassifier

from .IntentHandlers import IntentHandler
from .greeting_dataset import TRAINING_DATA


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _extrair_features(tokens: List[str]) -> dict:
    return {token: True for token in tokens}


class GreetingMLHandler(IntentHandler):

    def __init__(self, stemmer: RSLPStemmer):
        self._stemmer = stemmer
        self._classifier = self._treinar()

        self._rotulos_positivos = {"saudacao", "despedida"}


    def _treinar(self) -> NaiveBayesClassifier:
        conjunto_treino = []

        for texto, rotulo in TRAINING_DATA:
            tokens = self._tokenizar(texto)
            features = _extrair_features(tokens)
            conjunto_treino.append((features, rotulo))

        return NaiveBayesClassifier.train(conjunto_treino)

    def _tokenizar(self, texto: str) -> List[str]:
        normalizado = _normalizar(texto)
        tokens = normalizado.split()
        return [self._stemmer.stem(t) for t in tokens]

    def _raw_keywords(self) -> List[str]:
        return []

    def matches(self, tokens: List[str]) -> bool:
        if not tokens:
            return False

        features = _extrair_features(tokens)
        rotulo_predito = self._classifier.classify(features)
        return rotulo_predito in self._rotulos_positivos

    def get_intent_name(self) -> str:
        return "ask_greeting"