from huggingface_hub import InferenceClient
from learningModel.ILLMFallback import ILLMFallback

SYSTEM_PROMPT = """Você é o CineBot, um assistente especialista em filmes.
Responda sempre em português brasileiro, de forma conversacional e simpática.
Foque apenas em tópicos relacionados a filmes: sinopse, elenco, diretor, curiosidades, prêmios e recomendações.
Se a pergunta não for sobre filmes, redirecione educadamente para o tema."""

REFINE_PROMPT = """Você é o CineBot, um assistente simpático e conversacional sobre filmes.
Você receberá o contexto da conversa, a pergunta do usuário e uma resposta técnica gerada automaticamente.
Reescreva a resposta de forma natural e humanizada, em português brasileiro.

Regras obrigatórias:
- NÃO adicione frases introdutórias como "Sua pergunta me fez pensar...", "Que ótima pergunta!", "Claro!" ou similares.
- NÃO invente informações novas. Use APENAS o que está na resposta técnica fornecida.
- Mantenha TODAS as informações originais — apenas melhore o estilo.
- Vá direto ao ponto. A primeira palavra já deve ser sobre o conteúdo da resposta.
- Seja conciso."""

class HuggingFaceFallback(ILLMFallback):
    def __init__(self, token: str, model: str = "meta-llama/Llama-3.1-8B-Instruct"):
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
            return self._truncate_at_last_sentence(completion.choices[0].message.content.strip())
        except Exception as e:
            return f"Não consegui buscar uma resposta no momento. ({e})"

    def refine(self, question: str, raw_response: str, context: str = "") -> str:
        try:
            user_content = f"Pergunta original: {question}\n\nResposta para refinar: {raw_response}"
            if context:
                user_content = f"Contexto da conversa: {context}\n\n{user_content}"

            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": REFINE_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=200,
            )
            return self._truncate_at_last_sentence(completion.choices[0].message.content.strip())
        except Exception as e:
            return raw_response

    def _truncate_at_last_sentence(self, text: str) -> str:
        last_period = max(
            text.rfind("."),
            text.rfind("!"),
            text.rfind("?"),
        )
        if last_period == -1:
            return text  
        return text[:last_period + 1]