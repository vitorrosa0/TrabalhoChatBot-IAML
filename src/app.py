from dotenv import load_dotenv
import os

from TMDBRepository import TMDBRepository
from learningModel.HuggingFaceFallback import HuggingFaceFallback
from Orchestrator import ChatbotOrchestrator

load_dotenv()

def main():
    tmdb_key = os.getenv("TMDB_API_KEY")
    if not tmdb_key:
        print("Erro: TMDB_API_KEY não encontrada no .env")
        return

    repository = TMDBRepository(api_key=tmdb_key)

    token = os.getenv("HF_TOKEN")
    fallback = HuggingFaceFallback(token=token)

    bot = ChatbotOrchestrator(repository, fallback=fallback)

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

if __name__ == "__main__":
    main()