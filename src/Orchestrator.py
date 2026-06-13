import random
import re
from typing import List

from nlp import NLPProcessor, IntentClassifier, EntityExtractor, ResponseEnricher
from StateManagement import ConversationContext
from learningModel.ILLMFallback import ILLMFallback

class ChatbotOrchestrator:
    def __init__(self, repository, fallback: ILLMFallback = None):
        self.repository = repository
        self.fallback = fallback
        self.nlp_processor = NLPProcessor()
        self.intent_classifier = IntentClassifier(self.nlp_processor.stemmer)
        self.entity_extractor = EntityExtractor(repository)
        self.context = ConversationContext()
        self.enricher = ResponseEnricher()
        self.affirmation_handler = self.intent_classifier.get_affirmation_handler()

    def handle_message(self, user_text: str) -> dict:
        self.repository.reset_turno()
        self.context.last_user_text = user_text
        tokens, doc = self.nlp_processor.process_text(user_text)

        # Passa o texto original para que o PersonSearchHandler detecte nomes próprios
        intent = self.intent_classifier.classify(tokens, original_text=user_text)

        print(f"[DEBUG] tokens: {tokens}")
        print(f"[DEBUG] intent inicial: {intent}")

        # extrai título usando texto original sem stemming
        clean_text = self._extract_title_from_text(user_text, intent)
        PRONOUNS = {"ele", "ela", "dele", "dela", "esse", "essa", "este", "esta"}
        clean_words = set(clean_text.split())
        INTENTS_SEM_FILME = {
            "ask_greeting", "ask_affirmation", "ask_genre_search",
            "ask_country_search", "ask_person_search",
        }

        # ----- CORREÇÃO DO SEQUESTRO DE INTENT -----
        # Se o intent é country/genre mas o clean_text ainda tem palavras sobrando
        # (ex: "filme brasileiro Casa Grande"), o usuário quer um filme específico.
        if intent in ["ask_country_search", "ask_genre_search"] and clean_text and not clean_words.issubset(PRONOUNS):
            intent = "unknown"
            
        # Extrai ano da query
        year_match = re.search(r'\b(19|20)\d{2}\b', user_text)
        year_filter = year_match.group(0) if year_match else None

        # Extrai idioma/país da query para filtrar buscas
        LANG_MAP = {
            "brasileiro": "pt", "brasileira": "pt", "nacional": "pt",
            "americano": "en", "americana": "en", "inglês": "en", "inglesa": "en",
            "francês": "fr", "francesa": "fr",
            "italiano": "it", "italiana": "it",
            "espanhol": "es", "espanhola": "es",
            "coreano": "ko", "coreana": "ko",
            "japonês": "ja", "japonesa": "ja",
        }
        lang_filter = None
        for word in user_text.lower().split():
            if word in LANG_MAP:
                lang_filter = LANG_MAP[word]
                break

        # ----- DESAMBIGUAÇÃO DINÂMICA -----
        # Se não há keywords óbvias ou é um follow-up vago (e clean_text existe),
        # usamos o TMDB para descobrir se é pessoa ou filme
        if intent in ["unknown", "contextual_followup"] and clean_text and not clean_words.issubset(PRONOUNS):
            entity_type, entity_name = self.repository.resolve_ambiguous_query(clean_text)
            print(f"[DEBUG] resolve_ambiguous_query -> type: {entity_type}, name: {entity_name}")
            if entity_type == "person":
                intent = "ask_person_search"
                self.context.current_person = entity_name
            elif entity_type == "movie":
                # Trataremos a busca por título logo abaixo usando entity_name
                clean_text = entity_name
                if intent == "unknown":
                    intent = "contextual_followup"
        # -----------------------------------

        print(f"[DEBUG] intent após desambiguação: {intent}")

        movie_title = None
        is_new_movie = False
        # Recalcula clean_words após possível alteração de clean_text pela desambiguação
        clean_words = set(clean_text.split())
        # Se a frase tem muitas palavras funcionais de perguntas, provavelmente é uma pergunta para o LLM.
        QUESTION_WORDS = {"quem", "como", "onde", "porque", "por que", "qual", "quais", "quando", "quanto"}
        original_words = set(user_text.lower().split())
        is_question = bool(original_words.intersection(QUESTION_WORDS))

        if intent == "unknown" and is_question:
            pass # Não tenta extrair título de filme para evitar sequestro de contexto com n-grams aleatórios
        elif intent not in INTENTS_SEM_FILME and clean_text and not clean_words.issubset(PRONOUNS):
            movie_title = self.entity_extractor.extract_title(clean_text)
            if movie_title:
                movie = self.repository.get_movie_by_title(movie_title, year=year_filter, lang=lang_filter)
                if movie:
                    # Verifica se mudou o contexto
                    if self.context.current_movie is None or self.context.current_movie.title != movie.title or self.context.current_movie.year != movie.year:
                        is_new_movie = True
                    self.context.set_movie(movie)
            elif self.context.current_movie is None:
                # Título não encontrado e sem contexto anterior.
                # Tenta oferecer sugestões ao invés de passar para o LLM (que alucina).
                suggestions = self.repository.search_movie_suggestions(clean_text)
                if suggestions:
                    linhas = ["Encontrei alguns filmes com esse nome. Qual você quer saber mais?\n"]
                    for i, (titulo, ano) in enumerate(suggestions, 1):
                        linhas.append(f"{i}. **{titulo}** ({ano or '????'})")
                    linhas.append("\nMe diga o nome completo para eu buscar mais detalhes!")
                    return {"text": "\n".join(linhas), "source": "tmdb"}

        # Calcula a sub-intenção antes de checar repetição
        sub_intent = self._get_sub_intent(intent, tokens)
        full_intent = f"{intent}:{sub_intent}"

        # Repetição só quando intent E sub-intenção forem iguais
        is_repeat = (full_intent == self.context.last_full_intent and intent != "unknown")

        response = self._generate_response(intent, tokens, is_repeat=is_repeat, is_new_movie=is_new_movie)

        if is_new_movie and self.context.current_movie and self.context.current_movie.alternatives:
            alts = ", ".join(self.context.current_movie.alternatives)
            response += f"\n\n*(Obs: Encontrei outros filmes parecidos ou com mesmo nome: {alts}. Se o que encontrei não for o que você procura, repita o nome junto com o ano!)*"

        print(f"[DEBUG] response: {response}")
        print(f"[DEBUG] should_fallback: {self._should_use_fallback(intent, response)}")
        source = "local"

        if self._should_use_fallback(intent, response) and self.fallback:
            context_summary = self._build_context_summary()
            response = self.fallback.answer(user_text, context_summary)
            source = "llm"
        elif self.repository.foi_consultado():
            source = "tmdb"

        effective_intent = self.context.last_resolved_intent or intent
        self.context.last_resolved_intent = None
        response, hook_intent = self.enricher.enrich(effective_intent, response, self.context.current_movie)
        self.context.last_hook_intent = hook_intent
        self.context.last_full_intent = f"{effective_intent}:default" if intent == "ask_affirmation" else full_intent
        return {"text": response, "source": source}

    def _should_use_fallback(self, intent: str, response: str) -> bool:
        if "acionando assistente de ia" in response.lower() or "assistente de ia" in response.lower():
            return True
        if intent == "unknown":
            if self.context.current_movie and self.repository.foi_consultado():
                return False
            return True
        # Não acionar o LLM para intents reconhecidos que retornaram "não encontrei":
        # nesses casos a desambiguação ou mensagem de erro já foi tratada adequadamente.
        if intent in {"ask_person_search", "ask_genre_search", "ask_country_search",
                      "ask_greeting", "ask_affirmation"}:
            return False
        if "não encontrei" in response.lower() or "não tenho informações" in response.lower():
            return True
        return False

    def _build_context_summary(self) -> str:
        """Monta um resumo do contexto atual para enviar ao LLM."""
        parts = []
        if self.context.current_movie:
            m = self.context.current_movie
            parts.append(f"Filme em contexto: {m.title} ({m.year})")
            parts.append(f"Diretor: {m.director_name}")
            if m.synopsis:
                parts.append(f"Sinopse: {m.synopsis[:300]}")
            if m.cast:
                nomes = ", ".join(a.name for a in m.cast[:3])
                parts.append(f"Elenco principal: {nomes}")
            if m.genre:
                parts.append(f"Gênero: {', '.join(m.genre)}")
        if self.context.current_director:
            parts.append(f"Diretor em contexto: {self.context.current_director.name}")
        if self.context.last_topic:
            parts.append(f"Último tópico discutido: {self.context.last_topic}")
        if not parts:
            return "Nenhum contexto de conversa disponível ainda."
        return " | ".join(parts)

    def _generate_response(self, intent: str, tokens: List[str], is_repeat=False, is_new_movie=False) -> str:

        if intent == "ask_greeting":
            saudacoes = [
                "Olá! 🎬 Sou o CineBot, seu assistente de filmes.\n\nMe diga sobre qual filme você quer conversar — posso te contar a sinopse, diretor, elenco, curiosidades e muito mais.",
                "Oi! 🎬 Sou o CineBot, seu assistente de cinema.\n\nSobre qual filme você quer conversar hoje?",
                "Olá! 🎬 Bem-vindo ao CineBot.\n\nMe diga um filme e posso te contar sinopse, diretor, elenco, curiosidades e muito mais.",
            ]
            despedidas = [
                "Até logo! Foi um prazer conversar sobre cinema.",
                "Tchau! Volte quando quiser saber mais sobre algum filme.",
                "Até mais! Boas sessões de cinema!",
            ]
            tokens_despedida = {"tchau", "xau", "ate", "falou", "flw", "logo", "amanha"}
            if any(t in tokens for t in tokens_despedida):
                return random.choice(despedidas)
            return random.choice(saudacoes)

        if intent == "ask_affirmation":
            rotulo = self.affirmation_handler.get_label()
            ultimo = self.context.last_full_intent or ""

            if rotulo == "afirmacao" and ("ask_genre_search" in ultimo or "ask_country_search" in ultimo):
                texto_limpo = self.context.last_user_text
                for prefixo in ["sim, ", "sim ", "quero ", "quero ver ", "gostei do ", "o "]:
                    if texto_limpo.lower().startswith(prefixo):
                        texto_limpo = texto_limpo[len(prefixo):]
                        break
                print(f"[DEBUG] texto_limpo para extração: {texto_limpo}")
                movie_title = self.entity_extractor.extract_title(texto_limpo)
                print(f"[DEBUG] movie_title extraído: {movie_title}")
                if movie_title:
                    movie = self.repository.get_movie_by_title(movie_title)
                    if movie:
                        self.context.set_movie(movie)
                        return f"A sinopse de {movie.title} é: {movie.synopsis}"
                return "Qual filme da lista te interessa? Me diga o nome completo."

            if rotulo == "afirmacao":
                hook = self.context.last_hook_intent
                if hook:
                    self.context.last_hook_intent = None
                    self.context.last_resolved_intent = hook
                    return self._generate_response(hook, tokens)
                if "ask_trivia" in ultimo:
                    self.context.last_resolved_intent = "ask_trivia"
                    return self._generate_response("ask_trivia", tokens)
                if "ask_director" in ultimo:
                    self.context.last_resolved_intent = "ask_director"
                    return self._generate_response("ask_director", tokens)
                if "ask_awards" in ultimo:
                    self.context.last_resolved_intent = "ask_awards"
                    return self._generate_response("ask_awards", tokens)
                if "ask_cast" in ultimo:
                    self.context.last_resolved_intent = "ask_cast"
                    return self._generate_response("ask_cast", tokens)
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

        # ------------------------------------------------------------------
        # Busca por pessoa (ator / diretor)
        # ------------------------------------------------------------------
        if intent == "ask_person_search":
            # Dá prioridade ao nome desambiguado; senão usa o extrator antigo
            person_name = self.context.current_person or self.entity_extractor.extract_person_name(self.context.last_user_text)
            self.context.current_person = None  # Limpa o contexto
            if not person_name:
                return "Não consegui identificar o nome da pessoa. Poderia repetir com o nome completo?"

            filmes = self.repository.search_person_movies(person_name)
            if not filmes:
                return (
                    f"Não encontrei filmografia para **{person_name}** no momento. "
                    "Verifique a grafia do nome ou tente o nome em inglês."
                )

            linhas = [f"Encontrei alguns filmes com **{person_name}**:\n"]
            for i, (titulo, ano, personagem) in enumerate(filmes, 1):
                ano_str = ano if ano else "????"
                if personagem:
                    linhas.append(f"{i}. **{titulo}** ({ano_str}) — como _{personagem}_")
                else:
                    linhas.append(f"{i}. **{titulo}** ({ano_str})")
            linhas.append("\nQuer saber mais sobre algum desses filmes? Me diga o nome!")
            return "\n".join(linhas)

        if intent == "ask_genre_search":
            GENRE_STEMS = {
                "aca": "acao", "comed": "comedia", "dram": "drama",
                "terr": "terror", "suspens": "suspense", "romanc": "romance",
                "animaca": "animacao", "ficca": "ficcao", "avent": "aventura",
                "thrill": "thriller",
            }
            genre_keyword = next((GENRE_STEMS[t] for t in tokens if t in GENRE_STEMS), None)
            if not genre_keyword:
                return "Qual gênero você prefere? Posso buscar ação, drama, comédia, terror e muito mais."

            filmes = self.repository.get_movies_by_genre(genre_keyword)
            if not filmes:
                return "Não encontrei filmes desse gênero no momento. Tente outro gênero."

            genre_display = genre_keyword.replace('acao', 'ação').replace('animacao', 'animação').replace('ficcao', 'ficção científica')
            linhas = [f"Tenho alguns filmes de {genre_display} que podem te interessar:\n"]
            for i, (titulo, ano) in enumerate(filmes, 1):
                linhas.append(f"{i}. **{titulo}** ({ano or '????'})")
            linhas.append("\nAlgum te interessa? Me diga o nome e conto mais sobre ele!")
            return "\n".join(linhas)

        if intent == "ask_country_search":
            COUNTRY_STEMS = {
                "brasil": "brasileiro",
                "americ": "americano",
                "franc": "frances",
                "itali": "italiano",
                "espanhol": "espanhol",
                "core": "coreano",
                "japon": "japones",
            }
            COUNTRY_DISPLAY = {
                "brasileiro": "brasileiros",
                "americano": "americanos",
                "frances": "franceses",
                "italiano": "italianos",
                "espanhol": "espanhóis",
                "coreano": "coreanos",
                "japones": "japoneses",
            }
            country_keyword = next((COUNTRY_STEMS[t] for t in tokens if t in COUNTRY_STEMS), None)
            if not country_keyword:
                return "Qual país você prefere? Posso buscar filmes brasileiros, americanos, franceses e muito mais."

            filmes = self.repository.get_movies_by_country(country_keyword)
            if not filmes:
                return "Não encontrei filmes desse país no momento. Tente outro."

            country_display = COUNTRY_DISPLAY.get(country_keyword, country_keyword)
            linhas = [f"Tenho alguns filmes {country_display} que podem te interessar:\n"]
            for i, (titulo, ano) in enumerate(filmes, 1):
                linhas.append(f"{i}. **{titulo}** ({ano or '????'})")
            linhas.append("\nAlgum te interessa? Me diga o nome e conto mais sobre ele!")
            return "\n".join(linhas)

        movie = self.context.current_movie
        if not movie:
            return "Sobre qual filme você gostaria de conversar?"

        # 1. Tratamento de Repetição
        if is_repeat:
            if intent == "ask_director":
                return f"o diretor é o {movie.director_name}. Quer saber o estilo dele ou outros filmes?"
            if intent == "ask_synopsis":
                return "eu já te passei o resumo. Gostaria de saber uma curiosidade?"
            if intent == "ask_trivia":
                return "já te contei uma curiosidade. Quer saber outra ou prefere falar do diretor?"

        # 2. Lógica para o Diretor e Contexto
        if intent == "ask_director":
            director = self.repository.get_director_by_name(movie.director_name)
            if not director:
                return f"Não encontrei informações sobre o diretor de {movie.title}."

            self.context.set_director(director)

            if any(w in tokens for w in self._stem_list(["dirigiu", "lista", "filme"])):
                if director.filmography:
                    obras = ", ".join(director.filmography)
                    return f"Além de {movie.title}, {director.name} dirigiu: {obras}."

            if any(w in tokens for w in self._stem_list(["estilo", "jeito", "caracteristica"])):
                if director.style:
                    return f"O estilo do {director.name} foca em {director.style}."

            style_info = f" Ele é conhecido por {director.style}." if director.style else ""
            return f"O filme {movie.title} foi dirigido por {director.name}.{style_info}"

        if intent == "ask_synopsis":
            if not movie.synopsis or not movie.synopsis.strip():
                return f"Infelizmente não encontrei a sinopse de {movie.title} ({movie.year}). Talvez o filme ainda não tenha sido lançado."
            return f"A sinopse de {movie.title} é: {movie.synopsis}"

        if intent == "ask_trivia":
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
                    if director and director.style:
                        return f"O estilo do {director.name} foca em {director.style}."
                    elif director:
                        return f"Não tenho informações detalhadas sobre o estilo de {director.name}."
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
            if nominations > 0:
                return f"{movie.title} não ganhou Oscars, mas teve {nominations} indicações."
            return f"Não tenho informações sobre prêmios de {movie.title}."

        # ask_actor e ask_cast unificados — ambos retornam o elenco completo
        if intent in ("ask_actor", "ask_cast"):
            if not movie.cast:
                return f"Não tenho informações sobre o elenco de {movie.title}."
            membros = ", ".join(
                f"{membro.name} como {membro.role}" for membro in movie.cast
            )
            return f"O elenco de {movie.title} inclui: {membros}."

        if intent == "ask_actor_filmography":
            entities, _ = self.entity_extractor.extract(self.context.last_user_text)
            pessoa_mencionada = entities.get("person")
            ator = None
            if pessoa_mencionada and movie:
                ator = next(
                    (a for a in movie.cast if pessoa_mencionada in a.name.lower()),
                    None
                )

            if not ator:
                return "Não tenho informações locais sobre outros filmes do ator mencionado."

            if not ator.filmography:
                return f"Não encontrei outros filmes de {ator.name}."

            filmes = ", ".join(ator.filmography)
            return f"Além de {movie.title if movie else 'esse filme'}, {ator.name} participou de: {filmes}."

        if intent == "ask_similar":
            similares = self.repository.get_similar_movies(movie.title)
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

        if intent == "unknown" and movie:
            # Só retorna sinopse se o filme é novo neste turno;
            if is_new_movie:
                if not movie.synopsis or not movie.synopsis.strip():
                    return "Sobre qual filme você gostaria de conversar?"
                return f"A sinopse de {movie.title} é: {movie.synopsis}"
            else:
                return "Não tenho essa informação na minha base local. Acionando assistente de IA..."

        return "Interessante! Posso te falar sobre a sinopse, diretor ou curiosidades desse filme."


    def _stem_list(self, words: List[str]) -> List[str]:
        return [self.nlp_processor.stemmer.stem(w) for w in words]

    def _get_sub_intent(self, intent: str, tokens: List[str]) -> str:
        if intent != "ask_director":
            return "default"
        if any(w in tokens for w in self._stem_list(["dirigiu", "lista", "filme"])):
            return "filmography"
        if any(w in tokens for w in self._stem_list(["estilo", "jeito", "caracteristica"])):
            return "style"
        return "default"

    def _extract_title_from_text(self, text: str, intent: str) -> str:
        intent_keywords = set(self.intent_classifier.get_keywords_for_intent(intent))

        FUNCTIONAL_WORDS = {
            # Pronomes, partículas, conjunções
            "me", "te", "se", "um", "uma", "e",
            "de", "do", "da", "dos", "das", "no", "na", "por",
            "com", "que", "foi", "tem", "é",
            "qual", "quais", "como", "quando", "onde", "quanto", "quem",
            "curiosidade", "curiosidades",
            "sobre", "conte", "conta", "fale", "fala", "diga", "mostra",
            "filmes", "filme", "agora", "então", "depois", "antes", "já", "também",
            "está", "sim", "não", "você", "voce", "conhece",
            "quero", "queria", "gostaria", "assistir", "ver",
            "algo", "nada", "tudo", "ele", "ela", "fez", "fizeram", "faz",
            "dirigiu", "estrelou", "atuou", "participou", "outros", "outro",
            # Qualificadores de país/idioma — removidos para não poluir a busca
            "brasileiro", "brasileira", "americano", "americana",
            "francês", "francesa", "italiano", "italiana",
            "espanhol", "espanhola", "coreano", "coreana",
            "japonês", "japonesa", "nacional", "inglês", "inglesa",
        }

        text_clean = re.sub(r'[^\w\s]', '', self.nlp_processor.normalize(text))
        words = text_clean.split()

        title_words = [
            w for w in words
            if self.nlp_processor.stemmer.stem(w) not in intent_keywords
            and w not in FUNCTIONAL_WORDS
        ]

        # Remove artigos ("o", "a", "os", "as") apenas no INÍCIO.
        # Não removemos no meio pois podem ser parte do título (ex: "O Poderoso Chefão").
        # Mas se ficam no início, poluem a busca TMDB.
        while title_words and title_words[0] in {"o", "a", "os", "as"}:
            title_words.pop(0)

        return " ".join(title_words)