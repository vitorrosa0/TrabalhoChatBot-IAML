from typing import Optional


class ConversationContext:

    MORE_OF_SAME_REFS = [
        "quero outro", "me dá outro", "outro filme", "mais um",
        "próximo", "proximo", "não gostei", "nao gostei",
        "passa", "outra opção", "outra opcao", "diferente",
        "mais algum", "tem mais", "quero mais", "me indica outro",
        "não curti", "nao curti", "esse não", "esse nao",
        "tem outro", "tem mais algum", "tem outra opção",
        "outro", "outra", "mais alguma opção", "mais opções",
        "me manda outro", "me indica mais", "quero ver outro",
        "não quero esse", "nao quero esse", "me dá uma outra opção",
        "próxima opção", "proxima opcao", "e mais?", "tem mais?",
        "mais um filme", "manda outro", "me sugere outro",
        "me recomenda outro", "e agora?", "qual mais",
        "tem mais alguma coisa", "o que mais tem",
    ]

    DETAIL_REFS = [
        "me conta mais", "mais detalhes", "me fala mais",
        "fala sobre esse", "o que mais", "e sobre esse",
        "me conta sobre ele", "me fala dele",
    ]

    CONFIRMATION_REFS = [
        "sim", "yes", "pode", "quero", "vai", "claro", "manda",
        "manda ver", "pode ser", "bora", "ok", "isso", "exato",
        "com certeza", "por favor", "pfv", "pls", "manda um",
    ]

    def __init__(self, max_turns: int = 8):
        self._max_turns = max_turns
        self._history: list[dict] = []
        self.last_director: Optional[str] = None
        self.last_movie_title: Optional[str] = None
        self.last_genre: Optional[str] = None
        self.last_country: Optional[str] = None
        self.last_person_name: Optional[str] = None
        self.last_recommended_id: Optional[int] = None 
        self.last_recommended_genres: list[str] = [] 
        self._recently_recommended: list[int] = []

    def set_last_recommendation(self, movie_id: int, genres: list[str]):
        self.last_recommended_id = movie_id
        self.last_recommended_genres = genres
        if movie_id not in self._recently_recommended:
            self._recently_recommended.append(movie_id)
        if len(self._recently_recommended) > 10:
            self._recently_recommended.pop(0)

    def get_excluded_ids(self) -> list[int]:
        return list(self._recently_recommended)

    def is_more_of_same(self, text: str) -> bool:
        text_lower = text.lower().strip().rstrip("!?.")

        if any(ref in text_lower for ref in self.MORE_OF_SAME_REFS):
            return True

        has_active_context = any([
            self.last_director, self.last_genre,
            self.last_country, self.last_recommended_genres,
        ])
        if has_active_context:
            SHORT_TRIGGERS = [
                "outro", "outra", "mais", "próximo", "proximo",
                "next", "diferente", "muda", "troca", "passa",
                "e aí", "e ai", "continua", "e mais", "tem",
            ]
            if any(text_lower == t or text_lower.startswith(t + " ") for t in SHORT_TRIGGERS):
                return True

        return False

    def is_detail_request(self, text: str) -> bool:
        text_lower = text.lower()
        return any(ref in text_lower for ref in self.DETAIL_REFS)

    def update(self, user_message, intent, director=None, movie=None,
               genre=None, country=None, person=None):
        if director:
            self.last_director = director
            self.last_person_name = director
        if movie:
            self.last_movie_title = movie
        if genre:
            self.last_genre = genre
        if country:
            self.last_country = country
        if person and not director:
            self.last_person_name = person

        self._history.append({
            "message": user_message, "intent": intent,
            "director": director, "movie": movie,
            "genre": genre, "country": country,
        })
        if len(self._history) > self._max_turns:
            self._history.pop(0)

    def resolve_director_reference(self, text: str) -> Optional[str]:
        REFS = ["dele", "desse diretor", "do mesmo diretor", "desse cara",
                "desse cineasta", "filmes dele", "obras dele"]
        text_lower = text.lower()
        if any(r in text_lower for r in REFS):
            return self.last_director
        return None

    def resolve_movie_reference(self, text: str) -> Optional[str]:
        REFS = ["esse filme", "este filme", "parecido", "algo similar",
                "mais desse tipo", "como esse", "como este"]
        text_lower = text.lower()
        if any(r in text_lower for r in REFS):
            return self.last_movie_title
        return None

    def resolve_genre_reference(self, text: str) -> Optional[str]:
        REFS = ["desse gênero", "desse genero", "mais desse tipo",
                "desse estilo", "do mesmo gênero"]
        text_lower = text.lower()
        if any(r in text_lower for r in REFS):
            return self.last_genre
        return None

    def resolve_country_reference(self, text: str) -> Optional[str]:
        REFS = ["desse país", "desse pais", "do mesmo país", "do mesmo pais"]
        text_lower = text.lower()
        if any(r in text_lower for r in REFS):
            return self.last_country
        return None

    def last_intent(self) -> Optional[str]:
        return self._history[-1]["intent"] if self._history else None

    def is_confirmation(self, text: str) -> bool:
        text_stripped = text.lower().strip().rstrip("!?.")
        return text_stripped in self.CONFIRMATION_REFS

    def clear(self):
        self._history.clear()
        self.last_director = None
        self.last_movie_title = None
        self.last_genre = None
        self.last_country = None
        self.last_person_name = None
        self.last_recommended_id = None
        self.last_recommended_genres = []
        self._recently_recommended = []