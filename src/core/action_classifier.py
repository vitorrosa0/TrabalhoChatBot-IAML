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
        # ── Intenções diretas (Comandos de controle) ──────────────────────────
        if intencao == "saudacao": return "SAUDAR"
        if intencao == "despedida": return "DESPEDIR"
        if intencao == "ajuda": return "AJUDAR"
        if intencao == "mais_filmes": return "MAIS_FILMES"

        # ── Entidades Detectadas (Sementes) ───────────────────────────────────
        if (intencao == "consulta_entidade" or contexto.get("tipo_ref")) and contexto.get("nome_ref"):
            return "APRESENTAR_ENTIDADE"

        # ── Tratamentos específicos sem sessão ────────────────────────────────
        if contexto.get("genero_negado") and not state.tem_genero:
            return "GENERO_NEGADO"

        # ── Sistema de Pesos (Action Classifier Baseado em Score) ─────────────
        score = 0.0

        if state.tem_genero or contexto.get("genero_afirmado"):
            score += 1.0
        if state.tem_humor: score += 0.5
        if state.tem_acompanhado: score += 0.5
        if state.tem_duracao: score += 0.5
        if state.tem_disposicao: score += 0.5
        if state.tem_semente: score += 1.5

        # Não temos informação nenhuma
        if score == 0.0:
            if intencao == "recomendacao":
                return "PEDIR_GENERO"
            return "FALLBACK"

        # Temos uma base muito forte (Sessão completa ou Semente + Gênero/Humor)
        if score >= 3.0 or state.campos_preenchidos >= 5:
            return "RECOMENDAR_FINAL" if state.campos_preenchidos == 5 else "RECOMENDAR"

        # Se recebemos um gênero e não tínhamos sessão, devemos ir para RECOMENDAR para iniciar o fluxo
        if contexto.get("genero_afirmado") and not state.tem_genero:
            return "RECOMENDAR"

        # Temos alguma base intermediária (Gênero + 1 ou 2 slots)
        if score >= 1.5:
            return "RECOMENDAR"

        # Só temos o gênero na sessão, e o usuário está respondendo a próxima pergunta
        return "PEDIR_PROXIMO_CAMPO"