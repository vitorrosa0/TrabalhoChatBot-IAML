import json
from IMovieRepository import LocalJsonRepository
from Orchestrator import ChatbotOrchestrator


def main():
    with open('dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    repository = LocalJsonRepository(data)
    bot = ChatbotOrchestrator(repository)

    print("--- Bem-vindo ao CinemaBot (Beta) ---")
    print("Digite 'sair' para encerrar.\n")

    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        resposta = bot.handle_message(user_input)
        print(f"Bot: {resposta}\n")


if __name__ == "__main__":
    main()