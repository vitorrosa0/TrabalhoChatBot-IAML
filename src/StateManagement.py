from dataclasses import dataclass, field
from typing import Optional, List
from entitys import Movie, Actor, Director

@dataclass
class Message:
    role: str  # "user" ou "bot"
    content: str

class ConversationContext:
    def __init__(self):
        self.current_movie = None
        self.current_director = None
        self.current_actor = None
        self.last_topic = None
        self.last_intent = None  # Nova variável para rastrear a repetição
        self.history = []

    def set_movie(self, movie: Movie):
        self.current_movie = movie
        self.last_topic = "movie"
    
    def set_director(self, director: Director):
        self.current_director = director
        self.last_topic = "director"

    def add_message(self, role: str, content: str):
        self.history.append(Message(role=role, content=content))