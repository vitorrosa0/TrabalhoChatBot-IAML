from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from TMDBRepository import TMDBRepository
from learningModel.HuggingFaceFallback import HuggingFaceFallback
from Orchestrator import ChatbotOrchestrator

load_dotenv()

def criar_bot():
    tmdb_key = os.getenv("TMDB_API_KEY")
    if not tmdb_key:
        print("Erro: TMDB_API_KEY não encontrada no .env")
        sys.exit(1)
    token = os.getenv("HF_TOKEN")
    repository = TMDBRepository(api_key=tmdb_key)
    fallback = HuggingFaceFallback(token=token)
    return ChatbotOrchestrator(repository, fallback=fallback)


def modo_cli(bot):
    print("--- Bem-vindo ao CinemaBot (Beta) ---")
    print("Digite 'sair' para encerrar.\n")
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        resposta = bot.handle_message(user_input)
        tags = {"tmdb": " [TMDB]", "llm": " [LLM]", "local": ""}
        tag = tags.get(resposta["source"], "")
        print(f"Bot{tag}: {resposta['text']}\n")


def modo_web(bot):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    static_path = os.path.join(BASE_DIR, "src", "static")

    app = Flask(__name__, static_folder=static_path)

    @app.route("/")
    def index():
        return send_from_directory(static_path, "index.html")

    @app.route("/chat", methods=["POST"])
    def chat():
        data = request.get_json()
        mensagem = data.get("mensagem", "").strip()
        if not mensagem:
            return jsonify({"resposta": "Mensagem vazia.", "source": "local"}), 400
        resposta = bot.handle_message(mensagem)
        return jsonify({
            "resposta": resposta["text"],
            "source": resposta["source"],
        })

    @app.route("/api/destaques")
    def destaques():
        return jsonify([])

    app.run(debug=True, port=5000)

if __name__ == "__main__":
    bot = criar_bot()
    if "--web" in sys.argv:
        modo_web(bot)
    else:
        modo_cli(bot)