import os
from dotenv import load_dotenv
import time

from learningModel.HuggingFaceFallback import HuggingFaceFallback

load_dotenv()
token = os.getenv("HF_TOKEN")

# modelos a comparar
MODELS = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
]

# perguntas de teste
QUESTIONS = [
    ("quem compôs a trilha sonora de Interestelar?", "Filme em contexto: Interestelar"),
    ("quais outros filmes Christopher Nolan dirigiu?", "Filme em contexto: Interestelar | Diretor: Christopher Nolan"),
    ("por que Interestelar é considerado um marco da ficção científica?", "Filme em contexto: Interestelar"),
]

for model_name in MODELS:
    print(f"\n{'='*60}")
    print(f"MODELO: {model_name}")
    print('='*60)

    fallback = HuggingFaceFallback(token=token, model=model_name)

    for question, context in QUESTIONS:
        print(f"\nPergunta: {question}")
        inicio = time.time()
        resposta = fallback.answer(question, context)
        tempo = time.time() - inicio
        print(f"Resposta: {resposta}")
        print(f"Tempo: {tempo:.2f}s")