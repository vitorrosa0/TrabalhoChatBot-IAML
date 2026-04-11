import csv
import os
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

DATASET_PATH    = "dataset.csv"
MINIMO_TREINO   = 16
RETREINO_A_CADA = 5

COLUNAS = ["genero_pedido", "humor", "acompanhado", "duracao_preferida", "disposicao"]

CATEGORIAS = {
    "genero_pedido":     ["acao", "comedia", "drama", "terror", "romance",
                          "ficcao_cientifica", "animacao", "suspense"],
    "humor":             ["animado", "calmo", "entediado", "assustado", "romantico", "curioso", "triste"],
    "acompanhado":       ["sozinho", "amigos", "casal", "familia"],
    "duracao_preferida": ["curto", "medio", "longo"],
    "disposicao":        ["pensar", "curtir"],
    "genero_recomendado":["acao", "comedia", "drama", "terror", "romance",
                          "ficcao_cientifica", "animacao", "suspense"],
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
            linhas.append(tuple(row[c] for c in COLUNAS + ["genero_recomendado"]))
    return linhas

def salvar_exemplo(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, genero_recomendado):
    _inicializar_csv()

    # Garante newline no fim do arquivo antes de escrever
    with open(DATASET_PATH, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        if f.tell() > 0:
            f.seek(f.tell() - 1)
            if f.read(1) != "\n":
                f.write("\n")

    with open(DATASET_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([genero_pedido, humor, acompanhado, duracao_preferida, disposicao, genero_recomendado])

    dados = _carregar_csv()
    total = len(dados)
    if total >= MINIMO_TREINO and total % RETREINO_A_CADA == 0:
        _treinar(dados)

def codificar(linha):
    return [encoders[col].transform([val])[0] for col, val in zip(COLUNAS, linha)]

def preparar_dados():
    dados = _carregar_csv()
    X, y = [], []
    for row in dados:
        X.append(codificar(row[:5]))
        y.append(encoders["genero_recomendado"].transform([row[5]])[0])
    return np.array(X), np.array(y)

modelo_j48 = None
modelo_lmt = None

def _treinar(dados):
    global modelo_j48, modelo_lmt

    X = np.array([codificar(row[:5]) for row in dados])
    y = np.array([encoders["genero_recomendado"].transform([row[5]])[0]
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

def recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="j48"):
    entrada = codificar([genero_pedido, humor, acompanhado, duracao_preferida, disposicao])
    X_input = np.array([entrada])

    if modelo == "lmt":
        pred = modelo_lmt.predict(X_input)[0]
    else:
        pred = modelo_j48.predict(X_input)[0]

    return encoders["genero_recomendado"].inverse_transform([pred])[0]

def recomendar_com_ambos(genero_pedido, humor, acompanhado, duracao_preferida, disposicao):
    if not modelos_prontos():
        return None, None

    genero_j48 = recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="j48")
    genero_lmt = recomendar_com_ml(genero_pedido, humor, acompanhado, duracao_preferida, disposicao, modelo="lmt")
    return genero_j48, genero_lmt

_inicializar_csv()
dados_existentes = _carregar_csv()
if len(dados_existentes) >= MINIMO_TREINO:
    _treinar(dados_existentes)