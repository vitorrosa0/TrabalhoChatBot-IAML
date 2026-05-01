import spacy
from typing import List, Tuple

class NLPProcessor:
    def __init__(self):
        # Carrega o modelo do spaCy para Português
        self.nlp = spacy.load("pt_core_news_lg")

    def process_text(self, text: str):
        """
        Realiza a tokenização e lematização.
        Ex: "Quem dirigiu o filme?" -> ["quem", "dirigir", "o", "filme"]
        """
        doc = self.nlp(text.lower())
        tokens_lematizados = [token.lemma_ for token in doc]
        return tokens_lematizados, doc

    def extract_entities(self, doc) -> List[Tuple[str, str]]:
        """
        Extrai nomes de pessoas (PER) ou obras (MISC).
        """
        entities = []
        for ent in doc.ents:
            entities.append((ent.text, ent.label_))
        return entities