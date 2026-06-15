from abc import ABC, abstractmethod


class ILLMFallback(ABC):

    @abstractmethod
    def answer(self, question: str, context: str) -> str:
        """Responde uma pergunta que o NLP não conseguiu tratar (intent unknown)."""
        pass

    @abstractmethod
    def refine(self, question: str, raw_response: str, context: str = "") -> str:
        pass