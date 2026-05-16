from huggingface_hub import InferenceClient
from learningModel.ILLMFallback import ILLMFallback

SYSTEM_PROMPT = """Você é o CineBot, um assistente especialista em filmes.
Responda sempre em português brasileiro, de forma conversacional e simpática.
Foque apenas em tópicos relacionados a filmes: sinopse, elenco, diretor, curiosidades, prêmios e recomendações.
Se a pergunta não for sobre filmes, redirecione educadamente para o tema."""


class HuggingFaceFallback(ILLMFallback):
    def init(self, token: str, model: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self._client = InferenceClient(
            provider="auto",
            api_key=token,
        )
        self._model = model

    def answer(self, question: str, context: str) -> str:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Contexto: {context}\n\nPergunta: {question}"}
                ],
                max_tokens=200,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Não consegui buscar uma resposta no momento. ({e})"