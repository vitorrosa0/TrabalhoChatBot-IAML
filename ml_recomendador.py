import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
 
 
DADOS_TREINO = [
    ("jovem","acao","noite","fim_semana","animado","amigos","acao"),
    ("jovem","acao","noite","semana","animado","sozinho","acao"),
    ("jovem","ficcao_cientifica","noite","fim_semana","animado","amigos","acao"),
    ("adulto","acao","tarde","semana","animado","sozinho","acao"),
    ("adulto","acao","noite","fim_semana","animado","amigos","acao"),
    ("adulto","suspense","tarde","semana","curioso","sozinho","acao"),
    ("jovem","acao","manha","semana","entediado","sozinho","acao"),
    ("jovem","comedia","noite","fim_semana","entediado","amigos","comedia"),
    ("adulto","comedia","tarde","semana","entediado","sozinho","comedia"),
    ("idoso","comedia","tarde","fim_semana","calmo","familia","comedia"),
    ("jovem","animacao","noite","fim_semana","animado","amigos","comedia"),
    ("adulto","comedia","noite","fim_semana","animado","amigos","comedia"),
    ("jovem","comedia","tarde","semana","entediado","sozinho","comedia"),
    ("adulto","romance","tarde","fim_semana","calmo","casal","comedia"),
    ("adulto","drama","tarde","semana","calmo","sozinho","drama"),
    ("idoso","drama","tarde","semana","calmo","sozinho","drama"),
    ("adulto","drama","noite","semana","calmo","sozinho","drama"),
    ("idoso","romance","tarde","semana","calmo","sozinho","drama"),
    ("adulto","suspense","tarde","semana","curioso","sozinho","drama"),
    ("idoso","drama","manha","semana","calmo","sozinho","drama"),
    ("adulto","drama","tarde","fim_semana","calmo","casal","drama"),
    ("jovem","terror","noite","fim_semana","assustado","amigos","terror"),
    ("jovem","suspense","noite","fim_semana","animado","amigos","terror"),
    ("adulto","terror","noite","fim_semana","animado","amigos","terror"),
    ("jovem","terror","noite","semana","assustado","sozinho","terror"),
    ("jovem","terror","noite","fim_semana","curioso","amigos","terror"),
    ("adulto","terror","noite","fim_semana","assustado","amigos","terror"),
    ("jovem","ficcao_cientifica","noite","fim_semana","curioso","amigos","terror"),
    ("adulto","romance","noite","fim_semana","romantico","casal","romance"),
    ("jovem","romance","noite","fim_semana","romantico","casal","romance"),
    ("idoso","romance","tarde","fim_semana","calmo","casal","romance"),
    ("adulto","drama","noite","fim_semana","romantico","casal","romance"),
    ("adulto","romance","tarde","semana","romantico","sozinho","romance"),
    ("jovem","romance","noite","fim_semana","romantico","sozinho","romance"),
    ("idoso","romance","tarde","fim_semana","romantico","casal","romance"),
    ("jovem","ficcao_cientifica","noite","semana","curioso","sozinho","ficcao_cientifica"),
    ("adulto","ficcao_cientifica","noite","semana","curioso","sozinho","ficcao_cientifica"),
    ("jovem","ficcao_cientifica","noite","fim_semana","animado","amigos","ficcao_cientifica"),
    ("adulto","suspense","noite","semana","curioso","sozinho","ficcao_cientifica"),
    ("jovem","acao","noite","semana","curioso","sozinho","ficcao_cientifica"),
    ("adulto","ficcao_cientifica","tarde","semana","curioso","sozinho","ficcao_cientifica"),
    ("jovem","ficcao_cientifica","manha","semana","curioso","sozinho","ficcao_cientifica"),
    ("jovem","animacao","tarde","fim_semana","animado","familia","animacao"),
    ("idoso","animacao","tarde","fim_semana","calmo","familia","animacao"),
    ("adulto","animacao","tarde","fim_semana","animado","familia","animacao"),
    ("jovem","comedia","tarde","fim_semana","animado","familia","animacao"),
    ("adulto","animacao","manha","fim_semana","calmo","familia","animacao"),
    ("jovem","animacao","tarde","semana","entediado","sozinho","animacao"),
    ("idoso","comedia","tarde","fim_semana","calmo","familia","animacao"),
    ("adulto","suspense","noite","semana","curioso","sozinho","suspense"),
    ("jovem","suspense","noite","fim_semana","curioso","amigos","suspense"),
    ("adulto","drama","noite","semana","curioso","sozinho","suspense"),
    ("adulto","suspense","tarde","semana","calmo","sozinho","suspense"),
    ("jovem","terror","noite","semana","curioso","sozinho","suspense"),
    ("adulto","ficcao_cientifica","noite","semana","curioso","sozinho","suspense"),
    ("idoso","drama","tarde","semana","curioso","sozinho","suspense"),
]


COLUNAS = ["idade_usuario", "genero_favorito", "hora_do_dia",
           "dia_semana", "humor", "acompanhado"]
 
CATEGORIAS = {
    "idade_usuario":    ["jovem", "adulto", "idoso"],
    "genero_favorito":  ["acao", "comedia", "drama", "terror", "romance",
                         "ficcao_cientifica", "animacao", "suspense"],
    "hora_do_dia":      ["manha", "tarde", "noite"],
    "dia_semana":       ["semana", "fim_semana"],
    "humor":            ["animado", "calmo", "entediado", "assustado", "romantico", "curioso"],
    "acompanhado":      ["sozinho", "amigos", "casal", "familia"],
    "genero_recomendado": ["acao", "comedia", "drama", "terror", "romance",
                           "ficcao_cientifica", "animacao", "suspense"],
}
 
encoders = {col: LabelEncoder().fit(vals) for col, vals in CATEGORIAS.items()}
 
 
def codificar(linha):
    return [encoders[col].transform([val])[0] for col, val in zip(COLUNAS, linha)]
 
 
def preparar_dados():
    X, y = [], []
    for row in DADOS_TREINO:
        X.append(codificar(row[:6]))
        y.append(encoders["genero_recomendado"].transform([row[6]])[0])
    return np.array(X), np.array(y)
 
 
 
X, y = preparar_dados()
 
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
 
  
def recomendar_com_ml(idade, genero_favorito, hora, dia, humor, acompanhado,
                      modelo="j48"):
    """
    Usa J48 ou LMT para prever o gênero recomendado.
 
    Parâmetros:
        idade           : 'jovem' | 'adulto' | 'idoso'
        genero_favorito : 'acao' | 'comedia' | 'drama' | 'terror' |
                          'romance' | 'ficcao_cientifica' | 'animacao' | 'suspense'
        hora            : 'manha' | 'tarde' | 'noite'
        dia             : 'semana' | 'fim_semana'
        humor           : 'animado' | 'calmo' | 'entediado' |
                          'assustado' | 'romantico' | 'curioso'
        acompanhado     : 'sozinho' | 'amigos' | 'casal' | 'familia'
        modelo          : 'j48' | 'lmt'
 
    Retorna:
        string com o gênero recomendado
    """
    entrada = codificar([idade, genero_favorito, hora, dia, humor, acompanhado])
    X_input = np.array([entrada])
 
    if modelo == "lmt":
        pred = modelo_lmt.predict(X_input)[0]
    else:
        pred = modelo_j48.predict(X_input)[0]
 
    return encoders["genero_recomendado"].inverse_transform([pred])[0]
 
 
def recomendar_com_ambos(idade, genero_favorito, hora, dia, humor, acompanhado):
    """
    Roda os dois modelos e retorna o resultado de cada um.
    Útil para comparar ou usar votação entre eles.
    """
    genero_j48 = recomendar_com_ml(idade, genero_favorito, hora, dia, humor,
                                   acompanhado, modelo="j48")
    genero_lmt = recomendar_com_ml(idade, genero_favorito, hora, dia, humor,
                                   acompanhado, modelo="lmt")
    return genero_j48, genero_lmt
 