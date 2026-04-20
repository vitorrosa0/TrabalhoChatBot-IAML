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
    def __init__(
        self,
        movie_repo: MovieRepository,
        person_repo: PersonRepository,
        lexicon_repo: LexiconRepository,
        classifier: IntentClassifier,
        extractor: EntityExtractor,
    ):
        self._movies   = movie_repo
        self._people   = person_repo
        self._lexicon  = lexicon_repo
        self._classifier = classifier
        self._extractor  = extractor

        # cache de títulos para extração de entidades
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

        handlers = {
            "saudacao":        self._handle_greeting,
            "despedida":       self._handle_farewell,
            "recomendar_filme": self._handle_recommend,
            "buscar_diretor":  self._handle_director,
            "buscar_filme":    self._handle_movie_info,
            "sobre_genero":    self._handle_genre,
            "sobre_pais":      self._handle_country,
            "avaliacao":       self._handle_rating,
            "curiosidade":     self._handle_curiosity,
            "outro":           self._handle_other,
        }

        handler = handlers.get(intent, self._handle_unknown)
        return handler(user_message)

    # ── Heurísticas de fallback ───────────────────────────────────────────

    def _heuristic_intent(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ["recomend", "indica", "sugere", "assistir", "ver"]):
            return "recomendar_filme"
        if any(w in t for w in ["diretor", "dirigiu", "dirige", "realizador"]):
            return "buscar_diretor"
        if any(w in t for w in ["curiosidade", "curioso", "sabia", "fato", "você sabia"]):
            return "curiosidade"
        if any(w in t for w in ["sinopse", "sobre o filme", "me fala de", "o que é"]):
            return "buscar_filme"
        return None

    # ── Handlers de intenção ─────────────────────────────────────────────

    def _handle_greeting(self, text: str) -> str:
        return random.choice(GREETINGS)

    def _handle_farewell(self, text: str) -> str:
        return random.choice(FAREWELLS)

    def _handle_curiosity(self, text: str) -> str:
        return f"💡 {random.choice(CURIOSITIES)}"

    def _handle_other(self, text: str) -> str:
        responses = [
            "Sou o **CinemaBot**! 🎬 Um assistente especializado em cinema, criado para conversar sobre filmes, diretores e gêneros. Me pergunta algo sobre cinema!",
            "Me chamo **CinemaBot** — fui criado para ser seu guia no mundo do cinema. Posso recomendar filmes, falar de diretores, gêneros e curiosidades. O que você quer explorar?",
            "Sou o **CinemaBot**, seu companheiro cinéfilo! 🍿 Tenho um catálogo enorme de filmes. Quer uma recomendação ou quer papo sobre algum filme específico?",
        ]
        return random.choice(responses)

    def _handle_unknown(self, text: str) -> str:
        return random.choice(UNKNOWNS)

    def _handle_recommend(self, text: str) -> str:
        country = self._lexicon.resolve_country(text)
        genres  = self._extractor.extract_genres(text)
        person  = self._extractor.extract_person_name(text)
        year    = self._extractor.extract_year(text)

        candidates: List[Movie] = []

        # prioridade 1: diretor/pessoa mencionada
        if person:
            p = self._people.find_by_name(person)
            if p and p.filmes_conhecidos:
                candidates = [
                    self._movies.find_by_id(mid)
                    for mid in p.filmes_conhecidos
                ]
                candidates = [m for m in candidates if m]
            if candidates:
                movie = random.choice(candidates)
                return self._format_recommendation(
                    movie,
                    intro=f"Falando em {p.nome}! Que tal esse aqui:"
                )

        # prioridade 2: país + gênero
        if country and genres:
            by_country = self._movies.find_by_country(country)
            candidates = [m for m in by_country if any(g in m.generos for g in genres)]
            if candidates:
                movie = random.choice(candidates)
                label = self._lexicon.get_country_label(country)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(
                    movie,
                    intro=f"Achei um filme {label} de {genre_label} pra você:"
                )

        # prioridade 3: só país
        if country:
            candidates = self._movies.find_by_country(country)
            if candidates:
                movie = random.choice(candidates)
                label = self._lexicon.get_country_label(country)
                return self._format_recommendation(
                    movie,
                    intro=f"Que tal esse filme {label}?"
                )

        # prioridade 4: só gênero
        if genres:
            candidates = self._movies.find_by_multiple_genres(genres)
            if candidates:
                movie = random.choice(candidates)
                genre_label = self._extractor.slug_to_label(genres[0])
                return self._format_recommendation(
                    movie,
                    intro=f"Pra quem curte {genre_label}, esse aqui é top:"
                )

        # prioridade 5: ano mencionado
        if year:
            candidates = self._movies.find_by_year(year)
            if candidates:
                movie = random.choice(candidates)
                return self._format_recommendation(
                    movie,
                    intro=f"Um filme de {year} que vale muito a pena:"
                )

        # fallback: bem avaliados ou aleatório
        top = self._movies.find_top_rated(10)
        pool = top if top else self._movies.find_random(5)
        movie = random.choice(pool)
        return self._format_recommendation(
            movie,
            intro="Sem filtro específico, vou de um que está muito bem avaliado:"
        )

    def _handle_director(self, text: str) -> str:
        try:
            person_name = self._extractor.extract_person_name(text)

            if not person_name:
                top_directors = self._people.find_most_popular_directors(5)
                if top_directors:
                    names = ", ".join(d.nome for d in top_directors)
                    return (
                        f"Posso te falar sobre vários diretores! Alguns dos mais populares "
                        f"no catálogo: **{names}**. Qual te interessa?"
                    )
                return "Qual diretor você quer conhecer? Me diz o nome!"

            person = self._people.find_by_name(person_name)
            if not person:
                return (
                    f"Não encontrei **{person_name}** no meu catálogo ainda. "
                    f"Tenta outro nome ou me pede uma recomendação!"
                )

            role_label = "diretor" if person.is_director else "ator/atriz"

            # busca filmes pelo nome do diretor no repositório de filmes
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
                films_str = "Ainda não tenho filmes vinculados a essa pessoa no catálogo."

            return (
                f"**{person.nome}** é um renomado {role_label} com popularidade "
                f"{person.popularidade:.1f}/10. {films_str} "
                f"Quer saber mais ou que eu recomende um filme?"
            )
        except Exception as e:
            return "Não consegui buscar essa informação agora. Tenta de novo ou me pergunta outra coisa!"

    def _handle_movie_info(self, text: str) -> str:
        title = self._extractor.extract_movie_title(text, self._all_titles)

        if not title:
            return (
                "Qual filme você quer saber? Me diz o nome que eu busco as informações aqui!"
            )

        movie = self._movies.find_by_title(title)
        if not movie:
            return (
                f"Não encontrei *{title}* no catálogo. "
                f"Pode tentar com o nome original ou de outro jeito!"
            )

        return self._format_movie_detail(movie)

    def _handle_genre(self, text: str) -> str:
        genres = self._extractor.extract_genres(text)

        if not genres:
            all_labels = [
                "Ação", "Drama", "Comédia", "Terror", "Suspense",
                "Ficção Científica", "Crime", "Aventura", "Animação", "Romance"
            ]
            return (
                f"Adoro falar de gêneros! Tenho filmes de: {', '.join(all_labels)}. "
                f"Qual é o seu favorito? Posso recomendar algo específico!"
            )

        movies = self._movies.find_by_multiple_genres(genres)
        genre_labels = [self._extractor.slug_to_label(g) for g in genres]
        genre_str    = ", ".join(genre_labels)

        if not movies:
            return (
                f"Ainda não tenho filmes de **{genre_str}** no catálogo. "
                f"Mas posso recomendar outro gênero!"
            )

        sample = random.sample(movies, min(2, len(movies)))
        titles = " e ".join(f"*{m.titulo}*" for m in sample)

        return (
            f"**{genre_str}** tem muita coisa boa! Tenho {len(movies)} filme(s) assim "
            f"— {titles} são boas pedidas. Quer que eu recomende um?"
        )

    def _handle_country(self, text: str) -> str:
        country = self._lexicon.resolve_country(text)

        if not country:
            codes  = self._lexicon.all_codes()
            labels = [self._lexicon.get_country_label(c) for c in codes]
            return (
                f"Me diz de qual país você quer ver filmes! Conheço produções "
                f"{', '.join(labels[:6])} e mais."
            )

        movies = self._movies.find_by_country(country)
        label  = self._lexicon.get_country_label(country)

        if not movies:
            # avisa que o campo origem pode estar vazio no dataset
            sample = self._movies.find_random(3)
            lines  = "\n".join(f"• *{m.titulo}* ({m.ano})" for m in sample)
            return (
                f"Não encontrei filmes **{label}** com origem cadastrada no dataset. "
                f"O campo `origem` pode estar vazio nos dados. "
                f"Mas posso recomendar aleatoriamente:\n\n{lines}\n\n"
                f"Quer que eu recomende algo por gênero?"
            )

        sample = random.sample(movies, min(3, len(movies)))
        lines  = "\n".join(
            f"• *{m.titulo}* ({m.ano})"
            + (f" — ⭐ {m.avaliacao}" if m.avaliacao else "")
            for m in sample
        )

        return (
            f"Cinema **{label}** tem muito a oferecer! Alguns filmes:\n\n"
            f"{lines}\n\n"
            f"Quer saber mais sobre algum, ou que eu recomende um?"
        )

    def _handle_rating(self, text: str) -> str:
        top = self._movies.find_top_rated(5)

        if not top:
            pool = self._movies.find_random(5)
            lines = "\n".join(f"{i+1}. *{m.titulo}* ({m.ano})" for i, m in enumerate(pool))
            return (
                f"Ainda não tenho avaliações no catálogo, mas aqui vão alguns filmes:\n\n"
                f"{lines}\n\nQuer saber mais sobre algum?"
            )

        lines = "\n".join(
            f"{i+1}. *{m.titulo}* ({m.ano}) — ⭐ {m.avaliacao}/10"
            for i, m in enumerate(top)
        )
        return (
            f"Os filmes mais bem avaliados no catálogo:\n\n{lines}\n\n"
            f"Quer saber mais sobre algum deles?"
        )

    # ── Formatação de resposta ────────────────────────────────────────────

    def _format_recommendation(self, movie: Movie, intro: str) -> str:
        genres_label = ", ".join(
            self._extractor.slug_to_label(g) for g in movie.generos
        ) or "Gênero não informado"

        origem_label = (
            ", ".join(self._lexicon.get_country_label(o) for o in movie.origem)
            if movie.origem else "Origem não informada"
        )

        rating_str = f"⭐ {movie.avaliacao}/10" if movie.avaliacao else "sem avaliação no catálogo"
        sinopse_str = f"\n\n_{movie.sinopse}_" if movie.sinopse else ""

        return (
            f"{intro}\n\n"
            f"🎬 **{movie.titulo}** ({movie.ano})\n"
            f"**Gênero:** {genres_label} | **Origem:** {origem_label}\n"
            f"**Avaliação:** {rating_str}"
            f"{sinopse_str}\n\n"
            f"O que achou? Quer outro tipo de indicação ou mais detalhes?"
        )

    def _format_movie_detail(self, movie: Movie) -> str:
        genres_label = ", ".join(
            self._extractor.slug_to_label(g) for g in movie.generos
        ) or "Não informado"

        origem_label = (
            ", ".join(self._lexicon.get_country_label(o) for o in movie.origem)
            if movie.origem else "Não informada"
        )

        rating_str  = f"⭐ {movie.avaliacao}/10" if movie.avaliacao else "sem avaliação"
        diretor_str = f"\n**Diretor:** {movie.diretor}" if movie.diretor else ""
        elenco_str  = f"\n**Elenco:** {', '.join(movie.elenco[:3])}" if movie.elenco else ""
        sinopse_str = f"\n\n_{movie.sinopse}_" if movie.sinopse else ""

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