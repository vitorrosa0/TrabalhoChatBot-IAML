from src.core.state import ConversationState

# Ações possíveis — strings que o ActionRegistry vai mapear para classes
ACTIONS = {
    "SAUDAR",
    "DESPEDIR",
    "AJUDAR",
    "PEDIR_GENERO",
    "RECOMENDAR",          # trigger 1, 3 ou 5 — recomenda + pergunta próximo
    "RECOMENDAR_FINAL",    # sessão completa, grava no dataset
    "PEDIR_PROXIMO_CAMPO", # coleta campo sem recomendar
    "APRESENTAR_ENTIDADE", # filme/ator de referência detectado
    "MAIS_FILMES",         # usuário pediu mais do mesmo
    "GENERO_NEGADO",       # usuário rejeitou um gênero
    "FALLBACK",
}

class ActionClassifier:
    def classify(self, state: ConversationState, intencao: str, contexto: dict) -> str:
        # ── Intenções diretas ─────────────────────────────────────────────────
        if intencao == "saudacao":
            return "SAUDAR"

        if intencao == "despedida":
            return "DESPEDIR"

        if intencao == "ajuda":
            return "AJUDAR"

        if intencao == "mais_filmes":
            return "MAIS_FILMES"

        # ── Gênero negado sem sessão ativa ────────────────────────────────────
        if contexto.get("genero_negado") and not state.tem_genero:
            return "GENERO_NEGADO"

        # ── Semente detectada (filme ou ator de referência) ───────────────────
        if contexto.get("tipo_ref") and contexto.get("nome_ref"):
            return "APRESENTAR_ENTIDADE"

        # ── Sem gênero ainda ─────────────────────────────────────────────────
        if not state.tem_genero:
            if intencao == "recomendacao":
                return "PEDIR_GENERO"
            return "FALLBACK"

        # ── Sessão completa ───────────────────────────────────────────────────
        if state.campos_preenchidos == 5:
            return "RECOMENDAR_FINAL"

        # ── Triggers de recomendação: 1, 3 e 5 campos ────────────────────────
        if state.campos_preenchidos in {1, 3}:
            return "RECOMENDAR"

        # ── Coleta de campos intermediários ───────────────────────────────────
        return "PEDIR_PROXIMO_CAMPO"