import os
from dotenv import load_dotenv
import time

from learningModel.HuggingFaceFallback import HuggingFaceFallback

load_dotenv()
token = os.getenv("HF_TOKEN")

REFINE_PROMPT = """Você é o CineBot, um assistente simpático e conversacional sobre filmes.
Você receberá uma pergunta do usuário e uma resposta técnica gerada automaticamente.
Reescreva a resposta de forma natural e humanizada, em português brasileiro.
Comece reconhecendo a pergunta de forma leve e natural antes de responder.
REGRAS IMPORTANTES:
- Mantenha todos os dados exatos da resposta original: números, anos, nomes, categorias
- Não adicione informações que não estejam na resposta original
- Não invente detalhes como anos, categorias de prêmios, títulos de filmes ou detalhes da trama
- Não expanda sinopses além do que foi fornecido
- Apenas melhore o estilo e a fluidez do texto
- Escreva sempre em português brasileiro correto, sem erros de ortografia
Seja conciso."""
REFINE_CASES = [
    (
        "quem dirigiu?",
        "O filme Interestelar foi dirigido por Christopher Nolan. Ele é conhecido por Uso de efeitos práticos e estruturas narrativas não lineares."
    ),
    (
        "qual a sinopse?",
        "A sinopse de Interestelar é: Uma equipe de exploradores viaja através de um buraco de minhoca no espaço..."
    ),
    (
        "quais os prêmios?",
        "Interestelar ganhou 1 Oscar(s) e teve 5 indicações."
    ),
]

REFINE_MODELS = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
]

print("\n\n=== TESTE DE REFINAMENTO ===")
for model_name in REFINE_MODELS:
    print(f"\n{'='*60}")
    print(f"MODELO: {model_name}")
    print('='*60)

    fallback = HuggingFaceFallback(token=token, model=model_name)

    for question, raw in REFINE_CASES:
        print(f"\nPergunta: {question}")
        print(f"Resposta crua: {raw}")
        inicio = time.time()
        refined = fallback.refine(question, raw)
        tempo = time.time() - inicio
        print(f"Refinada: {refined}")
        print(f"Tempo: {tempo:.2f}s")