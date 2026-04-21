import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from src.repositories.movie_repository import MovieRepository
from src.repositories.person_repository import PersonRepository
from src.repositories.lexicon_repository import LexiconRepository
from src.nlp_engine.intent_classifier import IntentClassifier
from src.nlp_engine.entity_extractor import EntityExtractor
from src.service.chatbot_service import ChatbotService

DATASET = os.path.join(os.path.dirname(__file__), "data", "dataset_reconhecimento.json")

# repositórios e NLP são compartilhados (sem estado)
movie_repo   = MovieRepository(DATASET)
person_repo  = PersonRepository(DATASET)
lexicon_repo = LexiconRepository(DATASET)
classifier   = IntentClassifier()
known_people = [p.nome for p in person_repo.find_all()]
extractor    = EntityExtractor(known_people=known_people)

# contexto é por sessão
_sessions: dict[str, ChatbotService] = {}

def get_chatbot(session_id: str) -> ChatbotService:
    if session_id not in _sessions:
        _sessions[session_id] = ChatbotService(
            movie_repo, person_repo, lexicon_repo, classifier, extractor
        )
    return _sessions[session_id]

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data         = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    session_id   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"response": "Pode falar! Estou aqui. 😊"})

    chatbot  = get_chatbot(session_id)
    response = chatbot.respond(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    print(f"🎬 CinemaBot iniciando — {len(movie_repo.find_all())} filmes carregados")
    app.run(debug=True, port=5000)