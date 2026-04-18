from typing import Optional
from src.actions.base import BotAction
from src.nlp.generos import NOMES_GENEROS


class SaudarAction(BotAction):
    def execute(self, contexto, sid):
        return (
            "Olá! 🎬 Sou o CineBot, seu assistente de filmes!\n\n"
            "Me diz que gênero você quer assistir:\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense\n\n"
            "💡 Você também pode dizer:\n"
            "• \"Algo como Inception\"\n"
            "• \"Filmes com Tom Holland\"\n"
            "• \"Quero ação com o Brad Pitt\""
        ), sid


class DespedirAction(BotAction):
    def __init__(self, encerrar_fn):
        self._encerrar = encerrar_fn

    def execute(self, contexto, sid):
        if sid:
            self._encerrar(sid)
        return "Foi um prazer! Bom filme e até mais! 👋", None


class AjudarAction(BotAction):
    def execute(self, contexto, sid):
        return (
            "É simples! Me diga o gênero que você quer:\n\n"
            "• \"Quero ação\"\n"
            "• \"Me indica uma comédia\"\n\n"
            "Ou use referências:\n"
            "• \"Algo como Inception\" → filmes similares\n"
            "• \"Filmes com Tom Holland\" → filmografia do ator\n\n"
            "Gêneros: Ação, Comédia, Drama, Terror, Romance, "
            "Ficção Científica, Animação e Suspense."
        ), sid


class PedirGeneroAction(BotAction):
    def execute(self, contexto, sid):
        return (
            "Qual gênero você quer? 🎬\n"
            "Ação, Comédia, Drama, Terror, Romance, "
            "Ficção Científica, Animação ou Suspense.\n\n"
            "💡 Ou tente:\n"
            "• \"Algo como Inception\"\n"
            "• \"Filmes com Tom Holland\""
        ), sid

class GeneroBanidoAction(BotAction):
    def execute(self, contexto, sid):
        genero = contexto.get("genero_negado", "")
        nome   = NOMES_GENEROS.get(genero, genero)
        return (
            f"Entendido, sem **{nome}**! 😊 Que tal tentar outro gênero?\n\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense"
        ), sid


class FallbackAction(BotAction):
    def execute(self, contexto, sid):
        return (
            "Não entendi muito bem... 😅 "
            "Tente me dizer o gênero do filme que você quer!\n\n"
            "Gêneros: Ação, Comédia, Drama, Terror, "
            "Romance, Ficção Científica, Animação, Suspense."
        ), sid