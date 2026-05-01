from typing import List
from nlp import NLPProcessor, IntentClassifier, EntityExtractor
from StateManagement import ConversationContext


class ChatbotOrchestrator:
    def __init__(self, repository):
        self.repository = repository
        self.nlp_processor = NLPProcessor()
        self.intent_classifier = IntentClassifier(self.nlp_processor.stemmer)
        self.entity_extractor = EntityExtractor(repository)
        self.context = ConversationContext()

    def handle_message(self, user_text: str) -> str:
        tokens, doc = self.nlp_processor.process_text(user_text)
        intent = self.intent_classifier.classify(tokens)

        # print(f"[DEBUG] intent classificado: {intent}")
        # print(f"[DEBUG] last_topic: {self.context.last_topic}")
        entities, _ = self.entity_extractor.extract(user_text)

        if "movie" in entities:
            movie = self.repository.get_movie_by_title(entities["movie"])
            if movie:
                self.context.set_movie(movie)

        # Calcula a sub-intenção antes de checar repetição
        sub_intent = self._get_sub_intent(intent, tokens)
        full_intent = f"{intent}:{sub_intent}"

        # Repetição só quando intent E sub-intenção forem iguais
        is_repeat = (full_intent == self.context.last_full_intent and intent != "unknown")

        response = self._generate_response(intent, tokens, is_repeat=is_repeat)
        self.context.last_full_intent = full_intent
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

        if intent == "ask_director":
            director = self.repository.get_director_by_name(movie.director_name)
            if not director:
                return f"Não encontrei informações sobre o diretor de {movie.title}."
            
            self.context.set_director(director)  # sempre seta, independente da sub-intenção

            # Sub-intenção: filmografia
            if any(w in tokens for w in self._stem_list(["outro", "fez", "dirigiu", "lista", "filme"])):
                obras = ", ".join(director.filmography)
                return f"Além de {movie.title}, {director.name} dirigiu: {obras}."

            # Sub-intenção: estilo
            if any(w in tokens for w in self._stem_list(["estilo", "jeito", "caracteristica"])):
                return f"O estilo do {director.name} foca em {director.style}."

            # Resposta padrão
            return (
                f"O filme {movie.title} foi dirigido por {director.name}. "
                f"Ele é conhecido por {director.style}."
            )

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

        if intent == "ask_year":
            return f"{movie.title} foi lançado em {movie.year}."

        if intent == "ask_genre":
            # "estilo" é ambíguo — resolve pelo contexto
            if any(w in tokens for w in self._stem_list(["estilo", "jeito"])):
                if self.context.last_topic == "director":
                    director = self.repository.get_director_by_name(movie.director_name)
                    return f"O estilo do {director.name} foca em {director.style}."
                # contexto é filme — cai para resposta de gênero abaixo
            
            genres = ", ".join(movie.genre)
            return f"{movie.title} é um filme de {genres}."

        if intent == "contextual_followup":
            if self.context.last_topic == "director":
                director = self.repository.get_director_by_name(movie.director_name)
                if director:
                    return f"O {director.name} é conhecido por {director.style}. Quer saber mais sobre a filmografia dele?"
            if self.context.last_topic == "movie":
                return f"Sobre {movie.title}, posso te contar a sinopse, curiosidades ou falar do diretor. O que prefere?"
            return "Sobre o que exatamente você quer saber mais? Posso falar sobre a sinopse, diretor ou curiosidades."

        return "Interessante! Posso te falar sobre a sinopse, diretor ou curiosidades desse filme."


    def _stem_list(self, words: List[str]) -> List[str]:
        return [self.nlp_processor.stemmer.stem(w) for w in words]

    def _get_sub_intent(self, intent: str, tokens: List[str]) -> str:
        if intent != "ask_director":
            return "default"
        if any(w in tokens for w in self._stem_list(["outro", "fez", "dirigiu", "lista", "filme"])):
            return "filmography"
        if any(w in tokens for w in self._stem_list(["estilo", "jeito", "caracteristica"])):
            return "style"
        return "default"