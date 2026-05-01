from dataclasses import dataclass, field
from typing import Optional, List
from entitys import Movie, Actor, Director

@dataclass
class Message:
    role: str  # "user" ou "bot"
    content: str

class ConversationContext:
    def __init__(self):
        self.current_movie: Optional[Movie] = None
        self.current_director: Optional[Director] = None
        self.current_actor: Optional[Actor] = None
        self.last_topic: Optional[str] = None  # "movie", "director", "actor"
        self.history: List[Message] = []

    def set_movie(self, movie: Movie):
        self.current_movie = movie
        self.last_topic = "movie"
    
    def set_director(self, director: Director):
        self.current_director = director
        self.last_topic = "director"

    def add_message(self, role: str, content: str):
        self.history.append(Message(role=role, content=content))