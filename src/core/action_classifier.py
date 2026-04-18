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

        if intencao == "consulta_entidade" and contexto.get("tipo_ref") and contexto.get("nome_ref"):
            return "APRESENTAR_ENTIDADE"

        # ── Gênero negado sem sessão ativa ────────────────────────────────────
        if contexto.get("genero_negado") and not state.tem_genero:
            return "GENERO_NEGADO"

        # ── Semente detectada (filme ou ator de referência) ───────────────────
        if contexto.get("tipo_ref") and contexto.get("nome_ref"):
            return "APRESENTAR_ENTIDADE"

        # ── Sem gênero na sessão (mas o usuário pode ter citado o gênero nesta mensagem)
        if not state.tem_genero:
            if contexto.get("genero_afirmado"):
                return "RECOMENDAR"
            if intencao == "recomendacao":
                return "PEDIR_GENERO"
            return "FALLBACK"

        # ── Sessão completa ───────────────────────────────────────────────────
        if state.campos_preenchidos == 5:
            return "RECOMENDAR_FINAL"

        # ── Triggers de recomendação: com gênero + 1 slot (1) ou quase completo (4) ──
        if state.campos_preenchidos in {1, 4}:
            return "RECOMENDAR"

        # ── Coleta de campos intermediários ───────────────────────────────────
        return "PEDIR_PROXIMO_CAMPO"