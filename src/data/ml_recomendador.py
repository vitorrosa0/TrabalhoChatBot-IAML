import csv
import os
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from src.api.tmdb import MAPA_KEYWORDS

DATASET_PATH    = "data/dataset.csv"
MINIMO_TREINO   = 16
RETREINO_A_CADA = 5

TAGS_BASE = list(MAPA_KEYWORDS.keys())
COLUNAS_CATEGORICAS = ["genero_pedido", "humor", "acompanhado", "duracao_preferida", "disposicao"]
COLUNAS = COLUNAS_CATEGORICAS + TAGS_BASE
_GENEROS = [
    "acao", "aventura", "animacao", "cinema_tv", "comedia", "crime",
    "documentario", "drama", "familia", "fantasia", "faroeste",
    "ficcao_cientifica", "guerra", "historia", "misterio", "musica",
    "romance", "suspense", "terror",
]

CATEGORIAS = {
    "genero_pedido":     _GENEROS,
    "humor":             ["animado", "calmo", "entediado", "assustado", "romantico", "curioso", "triste"],
    "acompanhado":       ["sozinho", "amigos", "casal", "familia", "família"],
    "duracao_preferida": ["curto", "medio", "longo"],
    "disposicao":        ["pensar", "curtir"],
    "genero_recomendado": _GENEROS,
}

encoders = {col: LabelEncoder().fit(vals) for col, vals in CATEGORIAS.items()}

def _inicializar_csv():
    if not os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUNAS + ["genero_recomendado"])

def _carregar_csv():
    linhas = []
    if not os.path.exists(DATASET_PATH):
        return linhas
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                linha = []
                for c in COLUNAS_CATEGORICAS:
                    linha.append(row[c])
                for t in TAGS_BASE:
                    linha.append(row.get(t, "0") or "0")
                linha.append(row["genero_recomendado"])
                linhas.append(tuple(linha))
            except KeyError:
                continue
    return linhas

def salvar_exemplo(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, genero_recomendado, tags_usuario=None):
    if tags_usuario is None:
        tags_usuario = []
        
    _inicializar_csv()

    with open(DATASET_PATH, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        if f.tell() > 0:
            f.seek(f.tell() - 1)
            if f.read(1) != "\n":
                f.write("\n")

    linha = [genero_pedido, humor, acompanhado, duracao_preferida, disposicao]
    for tag in TAGS_BASE:
        linha.append(1 if tag in tags_usuario else 0)
    linha.append(genero_recomendado)

    with open(DATASET_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(linha)

    dados = _carregar_csv()
    total = len(dados)
    if total >= MINIMO_TREINO and total % RETREINO_A_CADA == 0:
        _treinar(dados)

def codificar(linha):
    codificado = []
    for i, val in enumerate(linha):
        if i < 5:
            col_nome = COLUNAS_CATEGORICAS[i]
            codificado.append(encoders[col_nome].transform([val])[0])
        else:
            # Para colunas de tags (binárias)
            codificado.append(int(val))
    return codificado

def preparar_dados():
    dados = _carregar_csv()
    X, y = [], []
    for row in dados:
        X.append(codificar(row[:-1]))
        y.append(encoders["genero_recomendado"].transform([row[-1]])[0])
    return np.array(X), np.array(y)

modelo_j48 = None
modelo_lmt = None

def _treinar(dados):
    global modelo_j48, modelo_lmt

    X = np.array([codificar(row[:-1]) for row in dados])
    y = np.array([encoders["genero_recomendado"].transform([row[-1]])[0]
                  for row in dados])

    modelo_j48 = DecisionTreeClassifier(
        criterion="entropy",
        min_samples_leaf=2,
        ccp_alpha=0.01,
        random_state=42
    )
    modelo_j48.fit(X, y)

    modelo_lmt = Pipeline([
        ("arvore", DecisionTreeClassifier(
            criterion="entropy",
            max_depth=4,
            min_samples_leaf=3,
            random_state=42
        )),
    ])
    modelo_lmt.fit(X, y)

def modelos_prontos():
    return modelo_j48 is not None and modelo_lmt is not None

def recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="j48", tags_usuario=None):
    if tags_usuario is None:
        tags_usuario = []
        
    linha = [genero_pedido, humor, acompanhado, duracao_preferida, disposicao]
    for tag in TAGS_BASE:
        linha.append(1 if tag in tags_usuario else 0)
        
    entrada = codificar(linha)
    X_input = np.array([entrada])

    if modelo == "lmt":
        pred = modelo_lmt.predict(X_input)[0]
    else:
        pred = modelo_j48.predict(X_input)[0]

    return encoders["genero_recomendado"].inverse_transform([pred])[0]

def recomendar_com_ambos(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, tags_usuario=None):
    if not modelos_prontos() or not genero_pedido:
        return None, None

    genero_j48 = recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="j48", tags_usuario=tags_usuario)
    genero_lmt = recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="lmt", tags_usuario=tags_usuario)
    return genero_j48, genero_lmt

_inicializar_csv()
dados_existentes = _carregar_csv()
if len(dados_existentes) >= MINIMO_TREINO:
    _treinar(dados_existentes)