from typing import List
from nlp import NLPProcessor, IntentClassifier, EntityExtractor, ResponseEnricher
from StateManagement import ConversationContext

class ChatbotOrchestrator:
    def __init__(self, repository):
        self.repository = repository
        self.nlp_processor = NLPProcessor()
        self.intent_classifier = IntentClassifier(self.nlp_processor.stemmer)
        self.entity_extractor = EntityExtractor(repository)
        self.context = ConversationContext()
        self.enricher = ResponseEnricher()
        self.affirmation_handler = self.intent_classifier.get_affirmation_handler()

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
        response = self.enricher.enrich(intent, response, self.context.current_movie)
        self.context.last_full_intent = full_intent
        return response

    def _generate_response(self, intent: str, tokens: List[str], is_repeat=False) -> str:
        import random

        if intent == "ask_greeting":
            saudacoes = [
                "Olá! Sou o CineBot. Posso te falar sobre sinopse, diretor, elenco ou curiosidades do Interestelar. O que prefere?",
                "Oi! Estou aqui para conversar sobre o Interestelar. Quer saber a sinopse, quem dirigiu ou alguma curiosidade?",
                "Olá! Pronto para falar de cinema. Pergunte sobre o Interestelar!",
             ]
            despedidas = [
                "Até logo! Foi um prazer conversar sobre cinema.",
                "Tchau! Volte quando quiser saber mais sobre o Interestelar.",
                "Até mais! Boas sessões de cinema!",
            ]
            tokens_despedida = {"tchau", "xau", "ate", "falou", "flw", "logo", "amanha"}
            if any(t in tokens for t in tokens_despedida):
                return random.choice(despedidas)
            return random.choice(saudacoes)
        
        if intent == "ask_affirmation":
            rotulo = self.affirmation_handler.get_label()
            ultimo = self.context.last_full_intent or ""

            if rotulo == "afirmacao":
                if "ask_trivia" in ultimo:
                    return self._generate_response("ask_trivia", tokens)
                if "ask_director" in ultimo:
                    return self._generate_response("ask_director", tokens)
                if "ask_awards" in ultimo:
                    return self._generate_response("ask_awards", tokens)
                if "ask_cast" in ultimo:
                    return self._generate_response("ask_cast", tokens)
                if "ask_synopsis" in ultimo:
                    return self._generate_response("ask_synopsis", tokens)
                return "Claro! Sobre o que você quer saber? Posso falar de sinopse, diretor, elenco ou curiosidades."
 
            else:
                topicos = {
                    "ask_synopsis":  "Quer saber uma curiosidade ou falar do diretor?",
                    "ask_director":  "Que tal conhecer o elenco ou ver os prêmios que o filme ganhou?",
                    "ask_trivia":    "Posso falar do elenco ou dos prêmios que o filme recebeu. O que prefere?",
                    "ask_awards":    "Posso falar do diretor ou contar uma curiosidade dos bastidores. Qual prefere?",
                    "ask_cast":      "Que tal a sinopse ou algumas curiosidades de bastidores?",
                }
                for chave, sugestao in topicos.items():
                    if chave in ultimo:
                        return sugestao
                return "Tudo bem! Posso falar de sinopse, diretor, elenco ou curiosidades. O que prefere?"

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

        if intent == "ask_synopsis":
            return f"A sinopse de {movie.title} é: {movie.synopsis}"

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
        
        if intent == "ask_awards":
            awards = movie.awards
            if not awards:
                return f"Não tenho informações sobre prêmios de {movie.title}."
            oscars = awards.get("oscars", 0)
            nominations = awards.get("nominations", 0)
            if oscars > 0:
                return f"{movie.title} ganhou {oscars} Oscar(s) e teve {nominations} indicações."
            return f"{movie.title} não ganhou Oscars, mas teve {nominations} indicações."

        if intent == "ask_cast":
            if not movie.cast:
                return f"Não tenho informações sobre o elenco de {movie.title}."
            membros = ", ".join(
                f"{membro.name} como {membro.role}" for membro in movie.cast
            )
            return f"O elenco de {movie.title} inclui: {membros}."
        
        if intent == "ask_similar":
            similares = self.repository.get_similar_movies()
            if not similares:
                return f"Não tenho recomendações de filmes parecidos com {movie.title}."
            lista = ", ".join(similares)
            return f"Se você gostou de {movie.title}, talvez curta também: {lista}."

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