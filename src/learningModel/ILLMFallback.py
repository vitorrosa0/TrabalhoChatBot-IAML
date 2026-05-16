from abc import ABC, abstractmethod

class ILLMFallback(ABC):
    @abstractmethod
    def answer(self, pergunta: str, contexto: str) -> str:
        """
        Recebe a pergunta do usuário e um contexto resumido da conversa.
        Retorna a resposta gerada pelo LLM.
        """
        pass

    @abstractmethod
    def refine(self, question: str, raw_response: str) -> str:
        """
        Recebe a resposta anterior e um feedback do usuário.
        Retorna uma resposta refinada com base no feedback.
        """
        pass