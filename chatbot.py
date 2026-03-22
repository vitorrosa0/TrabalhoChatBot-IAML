import nltk
import random
import string
from filmes import FILMES, MAPA_GENEROS

# Baixa os recursos necessários do NLTK
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("rslp", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

# Inicializa o stemmer e as stopwords em português
stemmer = RSLPStemmer()
STOPWORDS_PT = set(stopwords.words("portuguese"))

# Stems dos gêneros pré-computados para comparação
STEMS_GENEROS = {}
for genero, palavras in MAPA_GENEROS.items():
    STEMS_GENEROS[genero] = [stemmer.stem(p) for p in palavras]


def preprocessar(texto):
    """
    Aplica pipeline de PLN:
    1. Lowercase
    2. Remove pontuação
    3. Tokenização
    4. Remoção de stopwords
    5. Stemming
    """
    # 1. Lowercase
    texto = texto.lower()

    # 2. Remove pontuação
    texto = texto.translate(str.maketrans("", "", string.punctuation))

    # 3. Tokenização
    tokens = word_tokenize(texto, language="portuguese")

    # 4. Remove stopwords
    tokens = [t for t in tokens if t not in STOPWORDS_PT]

    # 5. Stemming
    stems = [stemmer.stem(t) for t in tokens]

    return tokens, stems


def detectar_genero(tokens, stems):
    """
    Tenta identificar o gênero cinematográfico mencionado pelo usuário.
    Compara stems do input com stems das palavras-chave de cada gênero.
    """
    for genero, stems_genero in STEMS_GENEROS.items():
        for stem_input in stems:
            if stem_input in stems_genero:
                return genero
        # Também verifica tokens originais (para palavras curtas que o stemmer pode alterar)
        for token in tokens:
            if token in MAPA_GENEROS[genero]:
                return genero
    return None


def detectar_intencao(tokens, stems):
    """
    Identifica a intenção do usuário com base em palavras-chave.
    """
    palavras_saudacao = ["oi", "ola", "olá", "hey", "bom", "boa", "salve", "opa"]
    palavras_despedida = ["tchau", "ate", "adeus", "sair", "encerrar", "obrigado", "obrigada", "valeu"]
    palavras_ajuda = ["ajuda", "ajud", "help", "como", "que", "faz", "funciona", "usar"]
    palavras_recomendacao = ["recomendar", "recomend", "indicar", "indic", "sugerir", "sugir", "quero", "quer", "assistir", "assista", "ver", "mostre", "mostr"]

    for token in tokens:
        if token in palavras_saudacao:
            return "saudacao"
        if token in palavras_despedida:
            return "despedida"

    for stem in stems:
        if stem in [stemmer.stem(p) for p in palavras_ajuda]:
            return "ajuda"
        if stem in [stemmer.stem(p) for p in palavras_recomendacao]:
            return "recomendacao"

    return "desconhecida"


def recomendar_filmes(genero, quantidade=3):
    """
    Retorna uma lista de filmes aleatórios do gênero especificado.
    """
    filmes = FILMES.get(genero, [])
    selecionados = random.sample(filmes, min(quantidade, len(filmes)))
    return selecionados


def gerar_resposta(mensagem_usuario):
    """
    Função principal: recebe a mensagem do usuário e retorna a resposta do chatbot.
    """
    tokens, stems = preprocessar(mensagem_usuario)
    intencao = detectar_intencao(tokens, stems)
    genero = detectar_genero(tokens, stems)

    # --- Saudação ---
    if intencao == "saudacao":
        return (
            "Olá! 🎬 Sou o CineBot, seu assistente de recomendação de filmes!\n\n"
            "Posso te recomendar filmes de vários gêneros:\n"
            "• Ação • Comédia • Drama • Terror\n"
            "• Romance • Ficção Científica • Animação • Suspense\n\n"
            "É só me dizer o que você quer assistir!"
        )

    # --- Despedida ---
    if intencao == "despedida":
        return "Foi um prazer recomendar filmes pra você! 🎬 Bom filme e até mais! 👋"

    # --- Ajuda ---
    if intencao == "ajuda":
        return (
            "É simples! Me diga o tipo de filme que você quer assistir. Por exemplo:\n\n"
            "• \"Quero um filme de ação\"\n"
            "• \"Me recomenda uma comédia\"\n"
            "• \"Estou com medo, quero terror\"\n"
            "• \"Algo romântico para hoje à noite\"\n\n"
            "Gêneros disponíveis: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        )

    # --- Recomendação com gênero identificado ---
    if genero:
        filmes = recomendar_filmes(genero)
        nomes_generos = {
            "acao": "Ação", "comedia": "Comédia", "drama": "Drama",
            "terror": "Terror", "romance": "Romance",
            "ficcao_cientifica": "Ficção Científica",
            "animacao": "Animação", "suspense": "Suspense",
        }
        nome_genero = nomes_generos.get(genero, genero)
        resposta = f"🎬 Ótima escolha! Aqui estão {len(filmes)} filmes de **{nome_genero}** pra você:\n\n"
        for i, filme in enumerate(filmes, 1):
            resposta += f"{i}. **{filme['titulo']}** ({filme['ano']})\n"
            resposta += f"   _{filme['descricao']}_\n\n"
        resposta += "Quer recomendações de outro gênero? 😊"
        return resposta

    # --- Gênero não identificado mas parece recomendação ---
    if intencao == "recomendacao":
        return (
            "Hmm, não identifiquei o gênero que você quer! 🤔\n\n"
            "Tente me dizer algo como:\n"
            "• \"Quero ação\"\n"
            "• \"Me indica uma comédia\"\n"
            "• \"Sugere um suspense\"\n\n"
            "Gêneros disponíveis: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação e Suspense."
        )

    # --- Fallback ---
    return (
        "Não entendi muito bem... 😅 Mas posso te recomendar filmes!\n\n"
        "Tente dizer algo como:\n"
        "• \"Quero um filme de ação\"\n"
        "• \"Me recomenda uma comédia\"\n"
        "• \"Sugere ficção científica\"\n\n"
        "Gêneros: Ação, Comédia, Drama, Terror, Romance, Ficção Científica, Animação, Suspense."
    )
