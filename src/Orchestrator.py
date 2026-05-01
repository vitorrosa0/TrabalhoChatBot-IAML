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
        tokens, doc = self.nlp_processor.process_text(user_text)
        intent = self.intent_classifier.classify(tokens)
        entities, _ = self.entity_extractor.extract(user_text)  # Corrigido o unpack aqui

        if "movie" in entities:
            movie = self.repository.get_movie_by_title(entities["movie"])
            if movie:
                self.context.set_movie(movie)

        # NOVO: Verificamos se há keywords de "detalhes extras" antes da repetição
        is_asking_extra = any(word in tokens for word in ["outro", "filme", "fez", "estilo", "mais"])

        # Só tratamos como repetição se a intenção for a mesma E não houver pedido de info extra
        if intent == self.context.last_intent and intent != "unknown" and not is_asking_extra:
            return f"Como eu já te contei, {self._generate_response(intent, tokens, is_repeat=True)}"

        response = self._generate_response(intent, tokens)
        self.context.last_intent = intent
        return response

    def _generate_response(self, intent: str, tokens: List[str], is_repeat=False) -> str:
        movie = self.context.current_movie
        if not movie:
            return "Sobre qual filme você gostaria de conversar? Conheço bem o Interestelar."

        # 1. Tratamento de Repetição
        if is_repeat:
            if intent == "ask_director":
                return f"o diretor é o {movie.director_name}. Quer saber o estilo dele ou outros filmes?"
            if intent == "ask_synopsis":
                return "eu já te passei o resumo. Gostaria de saber uma curiosidade?"
            if intent == "ask_trivia":
                return "já te contei uma curiosidade. Quer saber outra ou prefere falar do diretor?"

        # 2. Lógica para o Diretor e Contexto
        is_about_director = intent in ["ask_director", "contextual_followup"] or \
                            (intent == "unknown" and any(
                                word in tokens for word in ["diretor", "fez", "outro", "estilo", "mais"]))

        if is_about_director:
            director = self.repository.get_director_by_name(movie.director_name)
            if director:
                self.context.set_director(director)

                # Checagem de "Outros Filmes"
                if any(word in tokens for word in ["outro", "fez", "filme", "dirigiu", "lista"]):
                    obras = ", ".join(director.filmography)
                    return f"Além de {movie.title}, {director.name} dirigiu: {obras}."

                # Checagem de "Estilo"
                if any(word in tokens for word in ["estilo", "jeito", "caracteristica"]):
                    return f"O estilo do {director.name} foca em {director.style}."

                # Resposta padrão
                return f"O filme {movie.title} foi dirigido por {director.name}. Ele é conhecido por {director.style}."

        # 3. Lógica de Sinopse
        if intent == "ask_synopsis":
            return f"A sinopse de {movie.title} é: {movie.synopsis}"

        # 4. Lógica de Curiosidade (Restaurada!)
        if intent == "ask_trivia":
            import random
            if movie.trivia:
                fact = random.choice(movie.trivia)
                return f"Uma curiosidade sobre {movie.title}: {fact}"
            return "Puxa, não encontrei nenhuma curiosidade específica sobre esse filme."

        # 5. Resposta Padrão (Fallback)
        return "Interessante! Posso te falar sobre a sinopse, diretor ou curiosidades desse filme."