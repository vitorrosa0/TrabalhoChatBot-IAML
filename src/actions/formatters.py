def formatar_lista_filmes(filmes: list) -> str:
    resultado = ""
    for i, filme in enumerate(filmes, 1):
        estrelas    = f" ⭐ {filme['nota']}/10" if filme.get("nota") else ""
        duracao_min = filme.get("duracao_min")
        if duracao_min:
            horas = duracao_min // 60
            mins  = duracao_min % 60
            info_duracao = f" ⏱ {horas}h{mins}min" if horas else f" ⏱ {mins}min"
        else:
            info_duracao = ""
        resultado += f"{i}. **{filme['titulo']}** ({filme['ano']}){estrelas}{info_duracao}\n"
        resultado += f"   _{filme['descricao']}_\n\n"
    return resultado