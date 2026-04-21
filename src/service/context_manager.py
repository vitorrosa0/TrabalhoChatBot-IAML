from typing import Optional


class ConversationContext:

    def __init__(self, max_turns: int = 5):
        self._max_turns = max_turns
        self._history: list[dict] = []  # últimas mensagens
        self.last_director: Optional[str] = None
        self.last_movie_title: Optional[str] = None
        self.last_genre: Optional[str] = None
        self.last_country: Optional[str] = None
        self.last_person_name: Optional[str] = None

    def update(
        self,
        user_message: str,
        intent: str,
        director: Optional[str] = None,
        movie: Optional[str] = None,
        genre: Optional[str] = None,
        country: Optional[str] = None,
        person: Optional[str] = None,
    ):
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
            "message": user_message,
            "intent": intent,
            "director": director,
            "movie": movie,
            "genre": genre,
            "country": country,
        })

        # mantém só os últimos N turnos
        if len(self._history) > self._max_turns:
            self._history.pop(0)

    def resolve_director_reference(self, text: str) -> Optional[str]:
        """
        Resolve referências como 'dele', 'desse diretor', 'do mesmo diretor'
        para o último diretor mencionado.
        """
        DIRECTOR_REFS = [
            "dele", "desse diretor", "do mesmo diretor", "do nolan",
            "desse cara", "desse cineasta", "deste diretor", "dele mesmo",
            "deste cineasta", "filmes dele", "obras dele",
        ]
        text_lower = text.lower()
        for ref in DIRECTOR_REFS:
            if ref in text_lower:
                return self.last_director
        return None

    def resolve_movie_reference(self, text: str) -> Optional[str]:
        """
        Resolve 'esse filme', 'ele', 'desse', 'parecido com esse' para
        o último filme mencionado.
        """
        MOVIE_REFS = [
            "esse filme", "este filme", "parecido", "parecido com isso",
            "algo similar", "mais desse tipo", "como esse", "como este",
        ]
        text_lower = text.lower()
        for ref in MOVIE_REFS:
            if ref in text_lower:
                return self.last_movie_title
        return None

    def resolve_genre_reference(self, text: str) -> Optional[str]:
        """Resolve 'desse gênero', 'mais desse tipo' para o último gênero."""
        GENRE_REFS = [
            "desse gênero", "desse genero", "mais desse tipo",
            "desse estilo", "do mesmo gênero",
        ]
        text_lower = text.lower()
        for ref in GENRE_REFS:
            if ref in text_lower:
                return self.last_genre
        return None

    def resolve_country_reference(self, text: str) -> Optional[str]:
        """Resolve 'desse país', 'do mesmo país' para o último país."""
        COUNTRY_REFS = [
            "desse país", "desse pais", "do mesmo país",
            "do mesmo pais", "desse cinema",
        ]
        text_lower = text.lower()
        for ref in COUNTRY_REFS:
            if ref in text_lower:
                return self.last_country
        return None

    def last_intent(self) -> Optional[str]:
        if self._history:
            return self._history[-1]["intent"]
        return None

    def clear(self):
        self._history.clear()
        self.last_director = None
        self.last_movie_title = None
        self.last_genre = None
        self.last_country = None
        self.last_person_name = None