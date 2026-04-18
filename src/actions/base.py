from abc import ABC, abstractmethod
from typing import Optional, Tuple

class BotAction(ABC):
    @abstractmethod
    def execute(self, contexto: dict, sid: Optional[str]) -> Tuple[str, Optional[str]]:
        pass