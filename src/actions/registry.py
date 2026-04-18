class ActionRegistry:
    def __init__(self):
        self._actions = {}

    def registrar(self, nome: str, action: "BotAction"):
        self._actions[nome] = action

    def get(self, nome: str) -> "BotAction":
        return self._actions.get(nome)