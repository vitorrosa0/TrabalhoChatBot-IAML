import spacy
from spacy.pipeline import EntityRuler
from typing import Dict


class EntityExtractor:
    def __init__(self, repository):
        # Carrega o modelo de linguagem (lg é mais preciso para nomes)
        self.nlp = spacy.load("pt_core_news_lg")
        self.repository = repository
        self._setup_entity_ruler()

    def _setup_entity_ruler(self):
        """Adiciona regras baseadas na sua base de dados local."""
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = []
        # No futuro, você pode iterar por todos os filmes da base
        # Para o piloto, buscamos os dados do repository
        movie = self.repository.get_movie_by_title("Interestelar")
        if movie:
            patterns.append({"label": "FILME", "pattern": movie.title})

        director = self.repository.get_director_by_name("Christopher Nolan")
        if director:
            patterns.append({"label": "DIRETOR", "pattern": director.name})

        # Adiciona padrões para atores
        # Aqui você percorreria o cast do seu JSON
        patterns.append({"label": "ATOR", "pattern": "Matthew McConaughey"})

        ruler.add_patterns(patterns)

    def extract(self, text: str) -> Dict[str, str]:
        doc = self.nlp(text)
        entities = {}

        for ent in doc.ents:
            # Mapeia as labels para chaves que seu app.py entende
            if ent.label_ in ["FILME", "MISC"]:
                entities["movie"] = ent.text
            elif ent.label_ in ["DIRETOR", "ATOR", "PER"]:
                entities["person"] = ent.text

        return entities, doc