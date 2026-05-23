import json
from dotenv import load_dotenv
import os

from IMovieRepository import LocalJsonRepository
from learningModel.ILLMFallback import ILLMFallback
from learningModel.HuggingFaceFallback import HuggingFaceFallback
from Orchestrator import ChatbotOrchestrator

load_dotenv()

def main():
    with open('dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    repository = LocalJsonRepository(data)

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
        origem = "[Dataset]" if resposta["source"] == "dataset" else "[LLM]"
        print(f"Bot {origem}: {resposta['text']}\n")

if __name__ == "__main__":
    main()