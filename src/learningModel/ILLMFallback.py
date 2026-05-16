from abc import ABC, abstractmethod

class ILLMFallback(ABC):
    @abstractmethod
    def answer(self, pergunta: str, contexto: str) -> str:
        """
        Recebe a pergunta do usuário e um contexto resumido da conversa.
        Retorna a resposta gerada pelo LLM.
        """
        pass