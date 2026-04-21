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

        # ── Resolução contextual antes de despachar ──────────────────────
        # Se o usuário usou referência anafórica, enriquece a mensagem
        # internamente antes de processar.
        intent = self._resolve_context_intent(user_message, intent)

        handlers = {
            "saudacao":         self._handle_greeting,
            "despedida":        self._handle_farewell,
            "recomendar_filme": self._handle_recommend,
            "buscar_diretor":   self._handle_director,
            "buscar_filme":     self._handle_movie_info,
            "sobre_genero":     self._handle_genre,
            "sobre_pais":       self._handle_country,
            "avaliacao":        self._handle_rating,
            "curiosidade":      self._handle_curiosity,
            "outro":            self._handle_other,
        }

        handler = handlers.get(intent, self._handle_unknown)
        response = handler(user_message)

        # atualiza contexto após responder
        self._update_context(user_message, intent)

        return response

    # ── Resolução de contexto ─────────────────────────────────────────────

    def _resolve_context_intent(self, text: str, intent: str) -> str:
        """
        Detecta se o usuário está referenciando algo do contexto anterior
        e redireciona a intenção se necessário.
        """
        text_lower = text.lower()

        # "me recomende filmes dele / do Nolan / desse diretor"
        if self._ctx.resolve_director_reference(text) and intent in ("recomendar_filme", "outro", "buscar_diretor"):
            return "recomendar_pelo_contexto_diretor"

        # "me conta mais sobre esse filme" / "tem algo parecido?"
        if self._ctx.resolve_movie_reference(text) and intent in ("recomendar_filme", "buscar_filme", "outro"):
            return "recomendar_pelo_contexto_filme"

        # "mais filmes desse gênero"
        if self._ctx.resolve_genre_reference(text) and intent in ("recomendar_filme", "sobre_genero", "outro"):
            return "recomendar_pelo_contexto_genero"

        # "mais filmes desse país"
        if self._ctx.resolve_country_reference(text) and intent in ("recomendar_filme", "sobre_pais", "outro"):
            return "recomendar_pelo_contexto_pais"

        return intent

    def _update_context(self, text: str, intent: str):
        """Extrai entidades da mensagem e atualiza o contexto."""
        director = self._extractor.extract_person_name(text)
        movie    = self._extractor.extract_movie_title(text, self._all_titles)
        genres   = self._extractor.extract_genres(text)
        country  = self._lexicon.resolve_country(text)

        # se não extraiu diretor do texto mas é uma resposta de buscar_diretor,
        # mantém o contexto anterior
        self._ctx.update(
            user_message=text,
            intent=intent,
            director=director,
            movie=movie,
            genre=genres[0] if genres else None,
            country=country,
        )

    # ── Heurísticas ───────────────────────────────────────────────────────

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
                movie = random.choice(candidates)
                return self._format_recommendation(movie, intro=f"Falando em {p.nome}! Que tal:")

        if country and genres:
            by_country = self._movies.find_by_country(country)
            candidates = [m for m in by_country if any(g in m.generos for g in genres)]
            if candidates:
                movie = random.choice(candidates)
                label = self._lexicon.get_country_label(country)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(movie, intro=f"Achei um filme {label} de {genre_label}:")

        if country:
            candidates = self._movies.find_by_country(country)
            if candidates:
                movie = random.choice(candidates)
                label = self._lexicon.get_country_label(country)
                return self._format_recommendation(movie, intro=f"Que tal esse filme {label}?")

        if genres:
            candidates = self._movies.find_by_multiple_genres(genres)
            if candidates:
                movie = random.choice(candidates)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(movie, intro=f"Pra quem curte {genre_label}:")

        if year:
            candidates = self._movies.find_by_year(year)
            if candidates:
                movie = random.choice(candidates)
                return self._format_recommendation(movie, intro=f"Um filme de {year} que vale:")

        top  = self._movies.find_top_rated(10)
        pool = top if top else self._movies.find_random(5)
        movie = random.choice(pool)
        return self._format_recommendation(movie, intro="Que tal um dos mais bem avaliados:")

    def _handle_recommend_by_director_context(self, text: str) -> str:
        director_name = self._ctx.last_director
        if not director_name:
            return self._handle_recommend(text)

        candidates = self._movies.find_by_director(director_name)
        if not candidates:
            p = self._people.find_by_name(director_name)
            if p and p.filmes_conhecidos:
                candidates = [self._movies.find_by_id(mid) for mid in p.filmes_conhecidos]
                candidates = [m for m in candidates if m]

        if candidates:
            movie = random.choice(candidates)
            return self._format_recommendation(
                movie,
                intro=f"Claro! Um filme de **{director_name}** que você pode gostar:"
            )

        return f"Não encontrei outros filmes de **{director_name}** no catálogo. Quer que eu recomende algo parecido?"

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
            movie = random.choice(candidates)
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
            movie = random.choice(candidates)
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
            movie = random.choice(candidates)
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
                top_directors = self._people.find_most_popular_directors(5)
                if top_directors:
                    names = ", ".join(d.nome for d in top_directors)
                    return f"Alguns dos diretores mais populares no catálogo: **{names}**. Qual te interessa?"
                return "Qual diretor você quer conhecer? Me diz o nome!"

            person = self._people.find_by_name(person_name)
            if not person:
                return f"Não encontrei **{person_name}** no catálogo. Tenta outro nome!"

            role_label = "diretor" if person.is_director else "ator/atriz"
            filmes_do_diretor = self._movies.find_by_director(person.nome)

            if filmes_do_diretor:
                titles = ", ".join(f"*{m.titulo}* ({m.ano})" for m in filmes_do_diretor[:4])
                films_str = f"No catálogo, dirigiu: {titles}."
            elif person.filmes_conhecidos:
                movies = [self._movies.find_by_id(mid) for mid in person.filmes_conhecidos]
                movies = [m for m in movies if m]
                titles = ", ".join(f"*{m.titulo}* ({m.ano})" for m in movies)
                films_str = f"No catálogo, aparece em: {titles}."
            else:
                films_str = "Ainda não tenho filmes vinculados a essa pessoa."

            return (
                f"**{person.nome}** é um renomado {role_label} com popularidade "
                f"{person.popularidade:.1f}/10. {films_str} "
                f"Quer que eu recomende um filme dele?"
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
            f"O que achou? Quer outro tipo de indicação ou mais detalhes?"
        )

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