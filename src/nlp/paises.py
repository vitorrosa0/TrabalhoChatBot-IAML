from nltk.tokenize import word_tokenize
from src.nlp.pipeline import lematizar

MAPA_PAISES = {
    "BR": ["brasileiro","brasileira","brasileiros","brasileiras","brasil","nacional","nacionais"],
    "US": ["americano","americana","americanos","americanas","eua","hollywood"],
    "FR": ["francês","frances","francesa","franceses","francesas","franca"],
    "ES": ["espanhol","espanhola","espanhóis","espanhois","espanholas","espanha"],
    "IT": ["italiano","italiana","italianos","italianas","italia"],
    "JP": ["japonês","japones","japonesa","japoneses","japonesas","japao","japão","anime"],
    "KR": ["coreano","coreana","coreanos","coreanas","coreia","sul-coreano"],
    "MX": ["mexicano","mexicana","mexicanos","mexicanas","mexico","méxico"],
    "AR": ["argentino","argentina","argentinos","argentinas"],
    "IN": ["indiano","indiana","indianos","indianas","bollywood"],
    "NL": ["holandês","holandes","holandesa","holandeses","holandesas","holanda","neerlandês","neerlandes"],
}

NOMES_PAISES = {
    "BR": "brasileiros", "US": "americanos", "FR": "franceses",
    "ES": "espanhóis",   "IT": "italianos",  "JP": "japoneses",
    "KR": "coreanos",    "MX": "mexicanos",  "AR": "argentinos", "IN": "indianos",
    "NL": "holandeses",
}

LEMAS_PAISES = {
    codigo: [lematizar(p) for p in palavras]
    for codigo, palavras in MAPA_PAISES.items()
}

def detectar_pais(texto_bruto: str):
    tokens = word_tokenize(texto_bruto.lower(), language="portuguese")
    for codigo, lemas in LEMAS_PAISES.items():
        for token in tokens:
            if lematizar(token) in lemas or token in MAPA_PAISES[codigo]:
                return codigo
    return None