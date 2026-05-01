from typing import List
from nlp import NLPProcessor, IntentClassifier, EntityExtractor
from StateManagement import ConversationContext


class ChatbotOrchestrator:
    def __init__(self, repository):
        self.repository = repository
        self.nlp_processor = NLPProcessor()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor(repository)
        self.context = ConversationContext()

    def handle_message(self, user_text: str) -> str:
        # 1. Processamento Linguístico (Lematização)
        tokens, doc = self.nlp_processor.process_text(user_text)

        # 2. Identificação de Intenção e Entidades
        intent = self.intent_classifier.classify(tokens)
        entities, _ = self.entity_extractor.extract(user_text)

        # 3. Resolução de Entidade (Busca na base ou uso do contexto)
        # Se o usuário citou um filme, atualizamos o contexto
        if "movie" in entities:
            movie = self.repository.get_movie_by_title(entities["movie"])
            if movie:
                self.context.set_movie(movie)

        # 4. Execução da Intenção (Lógica de Resposta)
        return self._generate_response(intent, tokens)

    def _generate_response(self, intent: str, tokens: List[str]) -> str:
        # Se não houver filme em foco, pedimos para começar por um
        if not self.context.current_movie:
            return "Sobre qual filme você gostaria de conversar hoje? No momento, conheço bem o filme Interestelar."

        movie = self.context.current_movie

        # Lógica para cada Intent usando os dados do Repository
        if intent == "ask_synopsis":
            return f"A sinopse de {movie.title} é: {movie.synopsis}"

        elif intent == "ask_director":
            # Aqui usamos os dados do filme para chegar no diretor
            director = self.repository.get_director_by_name("Christopher Nolan")
            if director:
                self.context.set_director(director)
                return f"O filme {movie.title} foi dirigido por {director.name}. Ele tem um estilo focado em {director.style}"

        elif intent == "ask_trivia":
            import random
            trivia = random.choice(movie.trivia)
            return f"Uma curiosidade sobre {movie.title}: {trivia}"

        elif intent == "contextual_followup":
            # Se o usuário perguntou "e ele?" e o último tópico foi o diretor
            if self.context.last_topic == "director":
                return f"Além de {movie.title}, o Nolan também dirigiu {', '.join(self.context.current_director.filmography[:3])}."
            return "Pode me dar mais detalhes sobre o que você quer saber?"

        return "Interessante! Me conte mais ou pergunte sobre o diretor, elenco ou curiosidades do filme."