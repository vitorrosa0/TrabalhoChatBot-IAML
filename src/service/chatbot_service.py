"""
service/chatbot_service.py
Orquestra intenção + entidades + repositórios para produzir respostas conversacionais.
Responsabilidade única: lógica de diálogo e geração de resposta.
"""
import random
from typing import Optional, List
from src.models.movie import Movie
from src.repositories.movie_repository import MovieRepository
from src.repositories.person_repository import PersonRepository
from src.repositories.lexicon_repository import LexiconRepository
from src.nlp_engine.intent_classifier import IntentClassifier
from src.nlp_engine.entity_extractor import EntityExtractor
from src.service.context_manager import ConversationContext


CURIOSITIES = [
    "O filme com mais tempo de produção da história foi 'O Quixote' de Orson Welles — levou mais de 30 anos e ainda ficou inacabado.",
    "A trilha sonora de 'O Poderoso Chefão' foi composta por Nino Rota em apenas dois dias.",
    "Bong Joon-ho foi o primeiro diretor asiático a ganhar a Palma de Ouro e o Oscar de Melhor Filme no mesmo ano, com Parasita (2019/2020).",
    "Quentin Tarantino trabalhou numa videolocadora antes de ficar famoso — foi lá que consumiu filmes obsessivamente.",
    "Christopher Nolan filmou Interestelar consultando o físico Kip Thorne, que depois ganhou o Nobel de Física.",
    "O Clube da Luta foi um fracasso de bilheteria, mas se tornou um dos maiores cultos do DVD.",
    "Matrix foi produzido com US$ 63 milhões e arrecadou mais de US$ 460 milhões mundialmente.",
    "O primeiro filme da história, 'A Saída dos Operários da Fábrica Lumière', durava apenas 46 segundos.",
    "Cerca de 90% dos filmes mudos produzidos antes de 1929 estão perdidos para sempre.",
    "O Oscar de Melhor Filme estrangeiro só passou a incluir filmes em língua não-inglesa a partir de 1956.",
    "A palavra 'cinema' vem do grego 'kinema', que significa movimento.",
    "Stanley Kubrick era tão perfeccionista que filmou uma cena de 'O Iluminado' 127 vezes.",
]

GREETINGS = [
    "Oi! 🎬 Sou o CinemaBot, seu companheiro de conversas sobre cinema. O que você quer explorar hoje? Posso recomendar filmes, falar sobre diretores, gêneros... é só perguntar!",
    "Olá! Que bom ter você aqui. Tô cheio de papos sobre cinema pra te dar. Quer uma recomendação? Quer saber sobre algum diretor? Me conta!",
    "Ei! 🍿 Bem-vindo ao CinemaBot. Posso te ajudar com recomendações, informações sobre filmes ou curiosidades do cinema. O que você quer saber?",
    "Oi! Adoro quando aparecem cinéfilos pra conversar. Me diz — tá com vontade de ver algum tipo de filme, ou quer papo sobre cinema em geral?",
]

FAREWELLS = [
    "Foi ótimo conversar! Se quiser mais dicas de cinema, é só voltar. 🎬",
    "Até logo! Espero que você assista muita coisa boa. 🍿",
    "Valeu pela conversa! Boa sessão de cinema! 🎥",
    "Tchau! E lembre-se: a vida é muito melhor com bons filmes.",
]

UNKNOWNS = [
    "Hmm, não entendi bem. Você pode me perguntar sobre filmes, diretores, gêneros ou pedir uma recomendação!",
    "Não peguei essa. Tenta me perguntar sobre algum filme, gênero ou diretor — sou especialista nisso! 😄",
    "Essa eu não soube responder. Mas se falar de cinema, eu estou aqui!",
    "Puxa, acho que saímos um pouco do roteiro. Que tal a gente voltar a falar sobre cinema?",
    "Hmm, sobre isso eu ainda não tenho muito o que dizer. Mas se o assunto for filmes, pode mandar!",
    "Ops, me pegou de surpresa! Minha especialidade é a sétima arte. Quer uma indicação de filme?",
    "Acho que essa informação não está no meu script... mas se quiser falar sobre diretores ou gêneros, estou por aqui!",
    "Essa eu vou ficar devendo! Que tal mudarmos de assunto e explorarmos alguma recomendação de filme?",
    "Confesso que me perdi um pouco agora. Vamos voltar a falar de cinema? Me pede uma sugestão de filme!",
]


class ChatbotService:
    def __init__(self, movie_repo, person_repo, lexicon_repo, classifier, extractor):
        self._movies     = movie_repo
        self._people     = person_repo
        self._lexicon    = lexicon_repo
        self._classifier = classifier
        self._extractor  = extractor
        self._ctx        = ConversationContext()   # ← novo
        self._all_titles = [m.titulo for m in self._movies.find_all()] + \
                           [m.titulo_original for m in self._movies.find_all()]

    # ── Ponto de entrada ──────────────────────────────────────────────────

    def respond(self, user_message: str) -> str:
        intent     = self._classifier.predict(user_message)
        confidence = self._classifier.confidence(user_message)

        if confidence < 0.25:
            heuristic = self._heuristic_intent(user_message)
            if heuristic:
                intent = heuristic
            else:
                intent = "desconhecido" # <- Forçamos a ser desconhecido

        # ── Resolução contextual SEMPRE acontece, independente da confiança ──
        intent = self._resolve_context_intent(user_message, intent)

        handlers = {
            "saudacao":                         self._handle_greeting,
            "despedida":                        self._handle_farewell,
            "recomendar_filme":                 self._handle_recommend,
            "buscar_diretor":                   self._handle_director,
            "buscar_filme":                     self._handle_movie_info,
            "sobre_genero":                     self._handle_genre,
            "sobre_pais":                       self._handle_country,
            "avaliacao":                        self._handle_rating,
            "curiosidade":                      self._handle_curiosity,
            "outro":                            self._handle_other,
            "recomendar_pelo_contexto_diretor": self._handle_recommend_by_director_context,
            "recomendar_pelo_contexto_filme":   self._handle_recommend_by_movie_context,
            "recomendar_pelo_contexto_genero":  self._handle_recommend_by_genre_context,
            "recomendar_pelo_contexto_pais":    self._handle_recommend_by_country_context,
            "buscar_filme_contexto":            self._handle_movie_info_from_context,
        }

        handler = handlers.get(intent, self._handle_unknown)
        response = handler(user_message)
        self._update_context(user_message, intent)
        return response


    def _resolve_context_intent(self, text: str, intent: str) -> str:

        if self._ctx.is_confirmation(text):
            # se o contexto ativo é de pessoa → recomenda filme dela
            if self._ctx.last_director:
                return "recomendar_pelo_contexto_diretor"
            # se tem gênero ativo → recomenda do gênero
            if self._ctx.last_genre:
                return "recomendar_pelo_contexto_genero"
            # se tem país ativo → recomenda do país
            if self._ctx.last_country:
                return "recomendar_pelo_contexto_pais"
            # se tem filme ativo → recomenda similar
            if self._ctx.last_movie_title:
                return "recomendar_pelo_contexto_filme"
            # sem contexto → recomendação geral
            return "recomendar_filme"

        # ── "quero outro / passa / mais um" ──────────────────────────────────
        if self._ctx.is_more_of_same(text):
            if self._ctx.last_director:
                return "recomendar_pelo_contexto_diretor"
            if self._ctx.last_genre:
                return "recomendar_pelo_contexto_genero"
            if self._ctx.last_country:
                return "recomendar_pelo_contexto_pais"
            if self._ctx.last_recommended_genres:
                return "recomendar_pelo_contexto_filme"
            return "recomendar_filme"

        # ── "mais detalhes sobre esse" ────────────────────────────────────────
        if self._ctx.is_detail_request(text) and self._ctx.last_movie_title:
            return "buscar_filme_contexto"

        # ── Referências anafóricas explícitas ─────────────────────────────────
        if self._ctx.resolve_director_reference(text):
            return "recomendar_pelo_contexto_diretor"
        if self._ctx.resolve_movie_reference(text):
            return "recomendar_pelo_contexto_filme"
        if self._ctx.resolve_genre_reference(text):
            return "recomendar_pelo_contexto_genero"
        if self._ctx.resolve_country_reference(text):
            return "recomendar_pelo_contexto_pais"

        return intent

    def _update_context(self, text: str, intent: str):
        director = self._extractor.extract_person_name(text)
        movie    = self._extractor.extract_movie_title(text, self._all_titles)
        genres   = self._extractor.extract_genres(text)
        country  = self._lexicon.resolve_country(text)

        # se foi uma recomendação pelo contexto de diretor, não limpa o diretor
        # para permitir "quero outro dele" em seguida
        # mas se o usuário mudou de assunto explicitamente, limpa
        if intent in ("sobre_genero", "sobre_pais", "saudacao", "despedida"):
            self._ctx.last_director = None
            self._ctx.last_person_name = None

        self._ctx.update(
            user_message=text,
            intent=intent,
            director=director,
            movie=movie,
            genre=genres[0] if genres else None,
            country=country,
        )


    def _heuristic_intent(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ["recomend", "indica", "sugere", "assistir", "ver"]):
            return "recomendar_filme"
        if any(w in t for w in ["diretor", "dirigiu", "dirige", "realizador"]):
            return "buscar_diretor"
        if any(w in t for w in ["curiosidade", "curioso", "sabia", "fato"]):
            return "curiosidade"
        if any(w in t for w in ["sinopse", "sobre o filme", "me fala de", "o que é"]):
            return "buscar_filme"
        return None

    # ── Handlers ──────────────────────────────────────────────────────────

    def _handle_greeting(self, text: str) -> str:
        return random.choice(GREETINGS)

    def _handle_farewell(self, text: str) -> str:
        self._ctx.clear()
        return random.choice(FAREWELLS)

    def _handle_curiosity(self, text: str) -> str:
        return f"💡 {random.choice(CURIOSITIES)}"

    def _handle_other(self, text: str) -> str:
        responses = [
            "Sou o **CinemaBot**! 🎬 Um assistente especializado em cinema. Me pergunta sobre filmes, diretores ou gêneros!",
            "Me chamo **CinemaBot** — posso recomendar filmes, falar de diretores, gêneros e curiosidades. O que quer explorar?",
            "Sou o **CinemaBot**, seu companheiro cinéfilo! 🍿 Quer uma recomendação ou papo sobre algum filme?",
        ]
        return random.choice(responses)

    def _handle_unknown(self, text: str) -> str:
        return random.choice(UNKNOWNS)

    # ── Handlers contextuais (NOVOS) ──────────────────────────────────────

    def _handle_recommend(self, text: str) -> str:
        country = self._lexicon.resolve_country(text)
        genres  = self._extractor.extract_genres(text)
        person  = self._extractor.extract_person_name(text)
        year    = self._extractor.extract_year(text)

        candidates: List[Movie] = []

        if person:
            p = self._people.find_by_name(person)
            if p:
                candidates = self._movies.find_by_director(p.nome)
                if not candidates and p.filmes_conhecidos:
                    candidates = [self._movies.find_by_id(mid) for mid in p.filmes_conhecidos]
                    candidates = [m for m in candidates if m]
            if candidates:
                movie = self._pick_movie(candidates)
                if not movie:
                    return random.choice(UNKNOWNS)
                return self._format_recommendation(movie, intro=f"Falando em {p.nome}! Que tal:")

        if country and genres:
            by_country = self._movies.find_by_country(country)
            candidates = [m for m in by_country if any(g in m.generos for g in genres)]
            if candidates:
                movie = self._pick_movie(candidates)
                if not movie:
                    return random.choice(UNKNOWNS)
                label = self._lexicon.get_country_label(country)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(movie, intro=f"Achei um filme {label} de {genre_label}:")

        if country:
            candidates = self._movies.find_by_country(country)
            if candidates:
                movie = self._pick_movie(candidates)
                if not movie:
                    return random.choice(UNKNOWNS)
                label = self._lexicon.get_country_label(country)
                return self._format_recommendation(movie, intro=f"Que tal esse filme {label}?")

        if genres:
            candidates = self._movies.find_by_multiple_genres(genres)
            if candidates:
                movie = self._pick_movie(candidates)
                if not movie:
                    return random.choice(UNKNOWNS)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(movie, intro=f"Pra quem curte {genre_label}:")

        if year:
            candidates = self._movies.find_by_year(year)
            if candidates:
                movie = self._pick_movie(candidates)
                if not movie:
                    return random.choice(UNKNOWNS)
                return self._format_recommendation(movie, intro=f"Um filme de {year} que vale:")

        top  = self._movies.find_top_rated(10)
        pool = top if top else self._movies.find_random(5)
        movie = random.choice(pool)
        return self._format_recommendation(movie, intro="Que tal um dos mais bem avaliados:")

    def _handle_recommend_by_director_context(self, text: str) -> str:
        person_name = self._ctx.last_director
        if not person_name:
            return self._handle_recommend(text)

        # busca por diretor, elenco e filmes_conhecidos
        candidates = self._movies.find_by_director(person_name)

        if not candidates:
            candidates = self._movies.find_by_cast_member(person_name)

        if not candidates:
            p = self._people.find_by_name(person_name)
            if p and p.filmes_conhecidos:
                candidates = [self._movies.find_by_id(mid) for mid in p.filmes_conhecidos]
                candidates = [m for m in candidates if m]

        if candidates:
            movie = self._pick_movie(candidates)
            if movie:
                return self._format_recommendation(
                    movie,
                    intro=f"Um filme com **{person_name}**:"
                )

        return f"Não encontrei filmes com **{person_name}** no catálogo."

    def _handle_recommend_by_movie_context(self, text: str) -> str:
        title = self._ctx.last_movie_title
        if not title:
            return self._handle_recommend(text)

        ref_movie = self._movies.find_by_title(title)
        if not ref_movie:
            return self._handle_recommend(text)

        # recomenda por gênero similar
        candidates = self._movies.find_by_multiple_genres(ref_movie.generos)
        candidates = [m for m in candidates if m.titulo != ref_movie.titulo]

        if candidates:
            movie = self._pick_movie(candidates)
            if not movie:
                return random.choice(UNKNOWNS)
            genres_label = ", ".join(self._extractor.slug_to_label(g) for g in ref_movie.generos[:2])
            return self._format_recommendation(
                movie,
                intro=f"Se gostou de *{ref_movie.titulo}*, esse tem um estilo parecido ({genres_label}):"
            )

        return f"Não encontrei algo muito similar a *{ref_movie.titulo}* no catálogo agora."

    def _handle_recommend_by_genre_context(self, text: str) -> str:
        genre = self._ctx.last_genre
        if not genre:
            return self._handle_recommend(text)

        candidates = self._movies.find_by_genre(genre)
        if candidates:
            movie = self._pick_movie(candidates)
            if not movie:
                return random.choice(UNKNOWNS)
            label = self._extractor.slug_to_label(genre)
            return self._format_recommendation(
                movie,
                intro=f"Mais um de **{label}** pra você:"
            )

        return self._handle_recommend(text)

    def _handle_recommend_by_country_context(self, text: str) -> str:
        country = self._ctx.last_country
        if not country:
            return self._handle_recommend(text)

        candidates = self._movies.find_by_country(country)
        if candidates:
            movie = self._pick_movie(candidates)
            if not movie:
                return random.choice(UNKNOWNS)
            label = self._lexicon.get_country_label(country)
            return self._format_recommendation(
                movie,
                intro=f"Mais um filme {label}:"
            )

        return self._handle_recommend(text)

    def _handle_director(self, text: str) -> str:
        try:
            person_name = self._extractor.extract_person_name(text)

            if not person_name:
                top = self._people.find_most_popular(5)
                if top:
                    names = ", ".join(p.nome for p in top)
                    return f"Algumas pessoas populares no catálogo: **{names}**. Quer saber sobre alguma?"
                return "Qual ator ou diretor você quer conhecer? Me diz o nome!"

            person = self._people.find_by_name(person_name)
            if not person:
                return f"Não encontrei **{person_name}** no catálogo. Tenta outro nome!"

            role_labels = {
                "directing": "diretor",
                "acting": "ator/atriz",
                "writing": "roteirista",
                "production": "produtor",
            }
            role_label = role_labels.get(
                (person.departamento or "acting").lower(), "profissional de cinema"
            )

            # 1. tenta pelo campo diretor dos filmes
            filmes = self._movies.find_by_director(person.nome)

            # 2. tenta pelo campo elenco dos filmes
            if not filmes:
                filmes = self._movies.find_by_cast_member(person.nome)

            # 3. tenta pelos IDs em filmes_conhecidos
            if not filmes and person.filmes_conhecidos:
                filmes = [self._movies.find_by_id(mid) for mid in person.filmes_conhecidos]
                filmes = [m for m in filmes if m]

            if filmes:
                titles = ", ".join(f"*{m.titulo}* ({m.ano})" for m in filmes[:5])
                verbo  = "dirigiu" if person.is_director else "aparece em"
                films_str = f"No catálogo, {verbo}: {titles}."
            else:
                films_str = "Ainda não tenho filmes vinculados a essa pessoa no catálogo."

            return (
                f"**{person.nome}** é um(a) renomado(a) {role_label} "
                f"com popularidade {person.popularidade:.1f}/10. "
                f"{films_str} Quer que eu recomende um filme?"
            )
        except Exception:
            return "Não consegui buscar essa informação. Tenta de novo!"

    def _handle_movie_info(self, text: str) -> str:
        title = self._extractor.extract_movie_title(text, self._all_titles)
        if not title:
            return "Qual filme você quer saber? Me diz o nome!"
        movie = self._movies.find_by_title(title)
        if not movie:
            return f"Não encontrei *{title}* no catálogo."
        return self._format_movie_detail(movie)

    def _handle_movie_info_from_context(self, text: str) -> str:
        title = self._ctx.last_movie_title
        if not title:
            return self._handle_movie_info(text)
        movie = self._movies.find_by_title(title)
        if not movie:
            return self._handle_movie_info(text)
        return self._format_movie_detail(movie)

    def _handle_genre(self, text: str) -> str:
        genres = self._extractor.extract_genres(text)
        if not genres:
            all_labels = ["Ação","Drama","Comédia","Terror","Suspense","Ficção Científica","Crime","Aventura","Animação","Romance"]
            return f"Tenho filmes de: {', '.join(all_labels)}. Qual é o seu favorito?"

        movies = self._movies.find_by_multiple_genres(genres)
        genre_labels = [self._extractor.slug_to_label(g) for g in genres]
        genre_str = ", ".join(genre_labels)

        if not movies:
            return f"Ainda não tenho filmes de **{genre_str}** no catálogo."

        sample = random.sample(movies, min(2, len(movies)))
        titles = " e ".join(f"*{m.titulo}*" for m in sample)
        return (
            f"**{genre_str}** tem muita coisa boa! Tenho {len(movies)} filme(s) assim "
            f"— {titles} são ótimas pedidas. Quer que eu recomende um?"
        )

    def _handle_country(self, text: str) -> str:
        country = self._lexicon.resolve_country(text)
        if not country:
            codes  = self._lexicon.all_codes()
            labels = [self._lexicon.get_country_label(c) for c in codes]
            return f"De qual país você quer ver filmes? Tenho produções {', '.join(labels[:6])} e mais."

        movies = self._movies.find_by_country(country)
        label  = self._lexicon.get_country_label(country)
        label_pl = self._lexicon.get_country_label_plural(country)

        if not movies:
            sample = self._movies.find_random(3)
            lines  = "\n".join(f"• *{m.titulo}* ({m.ano})" for m in sample)
            return (
                f"Não encontrei filmes **{label}** com origem cadastrada. "
                f"Que tal explorar por gênero? Ou veja algumas sugestões:\n\n{lines}"
            )

        sample = random.sample(movies, min(3, len(movies)))
        lines  = "\n".join(
            f"• *{m.titulo}* ({m.ano})" + (f" — ⭐ {m.avaliacao}" if m.avaliacao else "")
            for m in sample
        )
        return (
            f"Cinema **{label}** tem muito a oferecer! Alguns filmes {label_pl}:\n\n"
            f"{lines}\n\nQuer saber mais sobre algum ou que eu recomende um?"
        )

    def _handle_rating(self, text: str) -> str:
        top = self._movies.find_top_rated(5)
        if not top:
            pool  = self._movies.find_random(5)
            lines = "\n".join(f"{i+1}. *{m.titulo}* ({m.ano})" for i, m in enumerate(pool))
            return f"Ainda sem avaliações no catálogo, mas aqui vão alguns:\n\n{lines}"
        lines = "\n".join(
            f"{i+1}. *{m.titulo}* ({m.ano}) — ⭐ {m.avaliacao}/10"
            for i, m in enumerate(top)
        )
        return f"Os mais bem avaliados no catálogo:\n\n{lines}\n\nQuer saber mais sobre algum?"

    # ── Formatação ────────────────────────────────────────────────────────

    def _format_recommendation(self, movie: Movie, intro: str) -> str:
        # registra no contexto para evitar repetição e resolver "quero outro"
        self._ctx.set_last_recommendation(movie.id, movie.generos)
        self._ctx.last_movie_title = movie.titulo

        genres_label = ", ".join(self._extractor.slug_to_label(g) for g in movie.generos) or "Não informado"
        origem_label = ", ".join(self._lexicon.get_country_label_plural(o) for o in movie.origem) if movie.origem else "Não informada"
        rating_str   = f"⭐ {movie.avaliacao}/10" if movie.avaliacao else "sem avaliação"
        sinopse_str  = f"\n\n_{movie.sinopse}_" if movie.sinopse else ""

        return (
            f"{intro}\n\n"
            f"🎬 **{movie.titulo}** ({movie.ano})\n"
            f"**Gênero:** {genres_label} | **Origem:** {origem_label}\n"
            f"**Avaliação:** {rating_str}"
            f"{sinopse_str}\n\n"
            f"O que achou? Quer outro ou mais detalhes?"
        )

    def _pick_movie(self, candidates: list) -> Optional[Movie]:
        """
        Escolhe um filme priorizando qualidade:
        1. Remove já recomendados nessa sessão
        2. Ordena por avaliação decrescente
        3. Sorteia entre os top 10 para ter variedade
        """
        excluded = self._ctx.get_excluded_ids()
        fresh = [m for m in candidates if m.id not in excluded]

        # se todos já foram recomendados, reseta histórico
        if not fresh:
            self._ctx._recently_recommended.clear()
            fresh = candidates

        if not fresh:
            return None

        # ordena por avaliação, filmes sem nota vão pro final
        fresh_sorted = sorted(fresh, key=lambda m: m.avaliacao or 0, reverse=True)

        # sorteia entre os top 10 para não ser sempre o mesmo
        pool = fresh_sorted[:10]
        return random.choice(pool)

    def _format_movie_detail(self, movie: Movie) -> str:
        genres_label = ", ".join(self._extractor.slug_to_label(g) for g in movie.generos) or "Não informado"
        origem_label = ", ".join(self._lexicon.get_country_label_plural(o) for o in movie.origem) if movie.origem else "Não informada"
        rating_str   = f"⭐ {movie.avaliacao}/10" if movie.avaliacao else "sem avaliação"
        diretor_str  = f"\n**Diretor:** {movie.diretor}" if movie.diretor else ""
        elenco_str   = f"\n**Elenco:** {', '.join(movie.elenco[:3])}" if movie.elenco else ""
        sinopse_str  = f"\n\n_{movie.sinopse}_" if movie.sinopse else ""

        return (
            f"🎬 **{movie.titulo}** ({movie.ano})\n"
            f"**Título original:** {movie.titulo_original}\n"
            f"**Gênero:** {genres_label} | **Origem:** {origem_label}\n"
            f"**Avaliação:** {rating_str}"
            f"{diretor_str}"
            f"{elenco_str}"
            f"{sinopse_str}\n\n"
            f"Quer que eu recomende algo parecido?"
        )