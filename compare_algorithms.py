"""
compare_algorithms.py
─────────────────────────────────────────────────────────────────────────────
Compara algoritmos de classificação de intenções do CinemaBot.
Gera métricas e salva gráficos em /outputs/

Uso:
    python compare_algorithms.py
    python compare_algorithms.py --output minha_pasta
"""

import argparse
import json
import os
import re
import warnings
warnings.filterwarnings("ignore")

import nltk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (
    cross_val_score, StratifiedKFold, learning_curve
)
from sklearn.metrics import (
    classification_report, confusion_matrix, ConfusionMatrixDisplay
)

for r in ["stopwords", "rslp", "punkt", "punkt_tab"]:
    nltk.download(r, quiet=True)

# ── Dataset de treino (mesmo do IntentClassifier) ─────────────────────────────

TRAINING_DATA = [
    # saudacao
    ("oi", "saudacao"), ("olá", "saudacao"), ("boa tarde", "saudacao"),
    ("bom dia", "saudacao"), ("boa noite", "saudacao"), ("hey", "saudacao"),
    ("e aí", "saudacao"), ("tudo bem", "saudacao"), ("oi tudo bem", "saudacao"),
    ("olá como vai", "saudacao"), ("salve", "saudacao"), ("oi bot", "saudacao"),
    ("oi, tudo bom?", "saudacao"), ("olá, como você está?", "saudacao"),

    # despedida
    ("tchau", "despedida"), ("até logo", "despedida"), ("até mais", "despedida"),
    ("valeu tchau", "despedida"), ("obrigado até mais", "despedida"),
    ("flw", "despedida"), ("falou", "despedida"), ("encerrando aqui", "despedida"),
    ("até breve", "despedida"), ("a gente se fala", "despedida"),

    # recomendar_filme
    ("me indica um filme", "recomendar_filme"),
    ("quero ver um filme", "recomendar_filme"),
    ("tem alguma recomendação", "recomendar_filme"),
    ("o que vale a pena assistir", "recomendar_filme"),
    ("me sugere algo para assistir", "recomendar_filme"),
    ("qual filme você recomenda", "recomendar_filme"),
    ("me recomenda um filme", "recomendar_filme"),
    ("quero indicação de filme", "recomendar_filme"),
    ("me indica algo bom", "recomendar_filme"),
    ("que filme assistir hoje", "recomendar_filme"),
    ("quero assistir algo novo", "recomendar_filme"),
    ("me recomenda um filme de ação", "recomendar_filme"),
    ("quero ver um drama", "recomendar_filme"),
    ("me sugere uma comédia", "recomendar_filme"),
    ("filmes brasileiros bons", "recomendar_filme"),
    ("algum filme coreano", "recomendar_filme"),
    ("me indica filme nacional", "recomendar_filme"),
    ("recomenda algo do nolan", "recomendar_filme"),
    ("tem filme do tarantino", "recomendar_filme"),
    ("quero ver algo japonês", "recomendar_filme"),
    ("me indica um terror", "recomendar_filme"),
    ("sugere um filme de aventura", "recomendar_filme"),
    ("boa indicação de ficção científica", "recomendar_filme"),
    ("me manda uma recomendação", "recomendar_filme"),
    ("o que tem de bom pra assistir", "recomendar_filme"),
    ("me indica um filme de suspense", "recomendar_filme"),
    ("quero um filme de ação americano", "recomendar_filme"),

    # buscar_diretor
    ("quem dirige esse filme", "buscar_diretor"),
    ("quem é o diretor", "buscar_diretor"),
    ("quem dirigiu", "buscar_diretor"),
    ("me fala do diretor", "buscar_diretor"),
    ("qual o diretor do filme", "buscar_diretor"),
    ("quem é fernando meirelles", "buscar_diretor"),
    ("me conta sobre o tarantino", "buscar_diretor"),
    ("filmes do christopher nolan", "buscar_diretor"),
    ("o nolan fez quais filmes", "buscar_diretor"),
    ("obras do kubrick", "buscar_diretor"),
    ("quais diretores estão no catálogo", "buscar_diretor"),
    ("diretores populares", "buscar_diretor"),
    ("me fala sobre o spielberg", "buscar_diretor"),
    ("me fala sobre o tarantino", "buscar_diretor"),
    ("quem é o tim burton", "buscar_diretor"),
    ("você conhece o chris evans", "buscar_diretor"),
    ("conhece o brad pitt", "buscar_diretor"),
    ("me fala do ryan gosling", "buscar_diretor"),
    ("quem é a scarlett johansson", "buscar_diretor"),
    ("sabe algo sobre o nolan", "buscar_diretor"),
    ("quem é esse ator", "buscar_diretor"),
    ("você sabe quem é", "buscar_diretor"),

    # buscar_filme
    ("fala sobre cidade de deus", "buscar_filme"),
    ("o que é pulp fiction", "buscar_filme"),
    ("me conta sobre matrix", "buscar_filme"),
    ("o que você sabe sobre parasita", "buscar_filme"),
    ("me fale do filme clube da luta", "buscar_filme"),
    ("conta a sinopse de interestelar", "buscar_filme"),
    ("de que se trata vingadores", "buscar_filme"),
    ("me fala de homem aranha", "buscar_filme"),
    ("o que é o auto da compadecida", "buscar_filme"),
    ("sinopse do filme", "buscar_filme"),
    ("me conta sobre esse filme", "buscar_filme"),
    ("qual a história de batman", "buscar_filme"),
    ("do que se trata a origem", "buscar_filme"),

    # sobre_genero
    ("me fala de filmes de terror", "sobre_genero"),
    ("gosto de drama", "sobre_genero"),
    ("prefiro comédia", "sobre_genero"),
    ("ação é meu favorito", "sobre_genero"),
    ("gosto de thriller", "sobre_genero"),
    ("ficção científica tem algum bom", "sobre_genero"),
    ("que gêneros você conhece", "sobre_genero"),
    ("crime me interessa", "sobre_genero"),
    ("gosto de suspense", "sobre_genero"),
    ("tem animação", "sobre_genero"),
    ("quero ver aventura", "sobre_genero"),
    ("filmes de fantasia", "sobre_genero"),
    ("me fala sobre o gênero romance", "sobre_genero"),
    ("adoro filmes de guerra", "sobre_genero"),

    # sobre_pais
    ("tem filme brasileiro", "sobre_pais"),
    ("quero algo nacional", "sobre_pais"),
    ("filmes americanos bons", "sobre_pais"),
    ("cinema coreano é top", "sobre_pais"),
    ("o que tem de francês", "sobre_pais"),
    ("cinema brasileiro", "sobre_pais"),
    ("produções nacionais", "sobre_pais"),
    ("algum filme da coreia", "sobre_pais"),
    ("cinema japonês", "sobre_pais"),
    ("filme mexicano", "sobre_pais"),
    ("produções indianas", "sobre_pais"),
    ("cinema argentino", "sobre_pais"),
    ("o que tem de italiano", "sobre_pais"),

    # avaliacao
    ("qual filme tem nota maior", "avaliacao"),
    ("o melhor filme da lista", "avaliacao"),
    ("qual tem melhor avaliação", "avaliacao"),
    ("o mais bem avaliado", "avaliacao"),
    ("qual tem o maior rating", "avaliacao"),
    ("nota do filme", "avaliacao"),
    ("qual vale mais a pena", "avaliacao"),
    ("melhores filmes do catálogo", "avaliacao"),
    ("top filmes", "avaliacao"),
    ("filme mais famoso", "avaliacao"),
    ("quais são os clássicos", "avaliacao"),

    # curiosidade
    ("me conta uma curiosidade", "curiosidade"),
    ("algo interessante sobre filmes", "curiosidade"),
    ("fact sobre cinema", "curiosidade"),
    ("me surpreende", "curiosidade"),
    ("alguma coisa aleatória sobre cinema", "curiosidade"),
    ("fato curioso", "curiosidade"),
    ("você sabia", "curiosidade"),
    ("me conta algo legal", "curiosidade"),
    ("curiosidade sobre filmes", "curiosidade"),

    # outro
    ("qual seu nome", "outro"), ("você é um bot", "outro"),
    ("quem te criou", "outro"), ("o que você faz", "outro"),
    ("como você funciona", "outro"), ("me ajuda", "outro"),
    ("quem é você", "outro"), ("você é uma ia", "outro"),
    ("como você foi feito", "outro"), ("o que é o cinemabot", "outro"),
    ("qual é o seu nome", "outro"), ("você é um robô", "outro"),
]

# ── Pré-processamento ─────────────────────────────────────────────────────────

_stemmer = RSLPStemmer()
try:
    _stops = set(stopwords.words("portuguese"))
except Exception:
    _stops = set()

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-záéíóúâêîôûãõç\s]", " ", text)
    tokens = [_stemmer.stem(t) for t in text.split() if t not in _stops]
    return " ".join(tokens)

# ── Algoritmos a comparar ─────────────────────────────────────────────────────

ALGORITHMS = {
    "Naive Bayes\n(MultinomialNB)": Pipeline([
        ("vec", CountVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", MultinomialNB(alpha=0.5)),
    ]),
    "Naive Bayes\n(ComplementNB)": Pipeline([
        ("vec", CountVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", ComplementNB(alpha=0.5)),
    ]),
    "Árvore de Decisão\n(J48 / CART)": Pipeline([
        ("vec", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", DecisionTreeClassifier(max_depth=20, random_state=42)),
    ]),
    "Random Forest": Pipeline([
        ("vec", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
    ]),
    "Regressão Logística\n(LMT)": Pipeline([
        ("vec", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
    ]),
    "SVM Linear": Pipeline([
        ("vec", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", LinearSVC(max_iter=2000, random_state=42)),
    ]),
    "Gradient Boosting": Pipeline([
        ("vec", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1,2))),
        ("clf", GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ]),
}

# ── Paleta ────────────────────────────────────────────────────────────────────

PALETTE = [
    "#e8b04b", "#c8403a", "#4b8be8", "#3ecf8e",
    "#b04be8", "#e84b8b", "#4be8c8",
]

BG      = "#0a0a0c"
SURFACE = "#111116"
CARD    = "#18181f"
BORDER  = "#2a2a38"
TEXT    = "#e8e6e0"
MUTED   = "#7a7880"

def apply_dark_style():
    plt.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    SURFACE,
        "axes.edgecolor":    BORDER,
        "axes.labelcolor":   TEXT,
        "xtick.color":       MUTED,
        "ytick.color":       MUTED,
        "text.color":        TEXT,
        "grid.color":        BORDER,
        "grid.alpha":        0.5,
        "font.family":       "monospace",
        "axes.titlesize":    13,
        "axes.labelsize":    11,
    })

# ── Avaliação ─────────────────────────────────────────────────────────────────

def evaluate_all(X, y, cv=5):
    skf     = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    results = {}
    print(f"\n{'─'*62}")
    print(f"{'Algoritmo':<35} {'Acurácia':>10} {'Desvio':>8} {'F1-macro':>10}")
    print(f"{'─'*62}")

    for name, pipeline in ALGORITHMS.items():
        label = name.replace("\n", " ")
        acc   = cross_val_score(pipeline, X, y, cv=skf, scoring="accuracy")
        f1    = cross_val_score(pipeline, X, y, cv=skf, scoring="f1_macro")
        results[name] = {"acc_mean": acc.mean(), "acc_std": acc.std(), "f1_mean": f1.mean()}
        print(f"{label:<35} {acc.mean():.4f}  ±{acc.std():.4f}   {f1.mean():.4f}")

    print(f"{'─'*62}")
    return results

# ── Gráfico 1: Acurácia por algoritmo ────────────────────────────────────────

def plot_accuracy(results, output_dir):
    apply_dark_style()
    names  = [n.replace("\n", "\n") for n in results]
    means  = [results[n]["acc_mean"] for n in results]
    stds   = [results[n]["acc_std"]  for n in results]
    colors = PALETTE[:len(names)]

    fig, ax = plt.subplots(figsize=(13, 6), facecolor=BG)
    bars = ax.bar(names, means, yerr=stds, capsize=5,
                  color=colors, edgecolor=BORDER, linewidth=0.8,
                  error_kw={"ecolor": MUTED, "elinewidth": 1.5})

    for bar, mean, std in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + std + 0.005,
                f"{mean:.3f}", ha="center", va="bottom",
                fontsize=9, color=TEXT, fontweight="bold")

    best_idx = means.index(max(means))
    bars[best_idx].set_edgecolor(PALETTE[0])
    bars[best_idx].set_linewidth(2.5)

    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Acurácia (cross-validation 5-fold)")
    ax.set_title("Comparação de Algoritmos — Classificação de Intenções\nCinemaBot NLP", pad=16)
    ax.yaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=9)

    fig.tight_layout()
    path = os.path.join(output_dir, "01_accuracy_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\n✓ Gráfico salvo: {path}")

# ── Gráfico 2: Acurácia vs F1-macro (scatter) ────────────────────────────────

def plot_scatter(results, output_dir):
    apply_dark_style()
    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG)

    for i, (name, r) in enumerate(results.items()):
        label = name.replace("\n", " ")
        ax.scatter(r["acc_mean"], r["f1_mean"],
                   color=PALETTE[i % len(PALETTE)], s=180,
                   zorder=5, edgecolors=TEXT, linewidths=0.6)
        ax.annotate(label, (r["acc_mean"], r["f1_mean"]),
                    textcoords="offset points", xytext=(8, 4),
                    fontsize=8, color=TEXT)

    ax.set_xlabel("Acurácia média (CV-5)")
    ax.set_ylabel("F1-macro médio (CV-5)")
    ax.set_title("Acurácia vs F1-macro por Algoritmo")
    ax.yaxis.grid(True, linestyle="--")
    ax.xaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)

    fig.tight_layout()
    path = os.path.join(output_dir, "02_accuracy_vs_f1.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"✓ Gráfico salvo: {path}")

# ── Gráfico 3: Matriz de confusão do melhor modelo ───────────────────────────

def plot_confusion(X, y, results, output_dir):
    apply_dark_style()
    best_name = max(results, key=lambda n: results[n]["acc_mean"])
    pipeline  = ALGORITHMS[best_name]
    pipeline.fit(X, y)
    y_pred = pipeline.predict(X)

    classes = sorted(set(y))
    cm      = confusion_matrix(y, y_pred, labels=classes)

    fig, ax = plt.subplots(figsize=(11, 9), facecolor=BG)
    sns.heatmap(cm, annot=True, fmt="d", cmap="YlOrRd",
                xticklabels=classes, yticklabels=classes,
                ax=ax, linewidths=0.5, linecolor=BG,
                cbar_kws={"shrink": 0.8})

    ax.set_title(f"Matriz de Confusão — {best_name.replace(chr(10), ' ')}\n(melhor modelo, treino completo)")
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.tick_params(axis="x", rotation=30, labelsize=9)
    ax.tick_params(axis="y", rotation=0,  labelsize=9)

    fig.tight_layout()
    path = os.path.join(output_dir, "03_confusion_matrix.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"✓ Gráfico salvo: {path}")
    return best_name

# ── Gráfico 4: Curva de aprendizado ──────────────────────────────────────────

def plot_learning_curves(X, y, results, output_dir):
    apply_dark_style()
    # plota apenas os 3 melhores
    sorted_names = sorted(results, key=lambda n: results[n]["acc_mean"], reverse=True)[:3]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=BG)
    fig.suptitle("Curvas de Aprendizado — Top 3 Algoritmos", fontsize=13, color=TEXT)

    for ax, name, color in zip(axes, sorted_names, PALETTE):
        pipeline = ALGORITHMS[name]
        sizes, train_scores, val_scores = learning_curve(
            pipeline, X, y,
            train_sizes=np.linspace(0.2, 1.0, 8),
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring="accuracy", n_jobs=-1,
        )

        t_mean = train_scores.mean(axis=1)
        t_std  = train_scores.std(axis=1)
        v_mean = val_scores.mean(axis=1)
        v_std  = val_scores.std(axis=1)

        ax.plot(sizes, t_mean, "o-", color=color,    label="Treino",   linewidth=2)
        ax.plot(sizes, v_mean, "s--", color=PALETTE[2], label="Validação", linewidth=2)
        ax.fill_between(sizes, t_mean-t_std, t_mean+t_std, alpha=0.15, color=color)
        ax.fill_between(sizes, v_mean-v_std, v_mean+v_std, alpha=0.15, color=PALETTE[2])

        ax.set_title(name.replace("\n", " "), fontsize=10)
        ax.set_xlabel("Exemplos de treino")
        ax.set_ylabel("Acurácia")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8)
        ax.yaxis.grid(True, linestyle="--")
        ax.set_axisbelow(True)

    fig.tight_layout()
    path = os.path.join(output_dir, "04_learning_curves.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"✓ Gráfico salvo: {path}")

# ── Gráfico 5: F1 por classe (melhor modelo) ─────────────────────────────────

def plot_f1_per_class(X, y, best_name, output_dir):
    apply_dark_style()
    pipeline = ALGORITHMS[best_name]
    pipeline.fit(X, y)
    y_pred   = pipeline.predict(X)

    report = classification_report(y, y_pred, output_dict=True)
    classes = [k for k in report if k not in ("accuracy","macro avg","weighted avg")]
    f1s     = [report[c]["f1-score"] for c in classes]

    sorted_pairs = sorted(zip(f1s, classes), reverse=True)
    f1s_s, cls_s = zip(*sorted_pairs)

    colors = [PALETTE[0] if f >= 0.9 else PALETTE[1] if f >= 0.7 else PALETTE[2]
              for f in f1s_s]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    bars = ax.barh(cls_s, f1s_s, color=colors, edgecolor=BORDER, linewidth=0.6)

    for bar, val in zip(bars, f1s_s):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}", va="center", fontsize=9, color=TEXT)

    ax.set_xlim(0, 1.12)
    ax.set_xlabel("F1-score")
    ax.set_title(f"F1-score por Intenção — {best_name.replace(chr(10), ' ')}")
    ax.xaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)

    legend = [
        mpatches.Patch(color=PALETTE[0], label="Excelente (≥0.90)"),
        mpatches.Patch(color=PALETTE[1], label="Bom (≥0.70)"),
        mpatches.Patch(color=PALETTE[2], label="Atenção (<0.70)"),
    ]
    ax.legend(handles=legend, fontsize=8, loc="lower right")

    fig.tight_layout()
    path = os.path.join(output_dir, "05_f1_per_class.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"✓ Gráfico salvo: {path}")

# ── Report JSON ───────────────────────────────────────────────────────────────

def save_report(results, best_name, output_dir):
    report = {
        "melhor_algoritmo": best_name.replace("\n", " "),
        "algoritmos": {
            name.replace("\n", " "): {
                "acuracia_media": round(r["acc_mean"], 4),
                "desvio_padrao":  round(r["acc_std"],  4),
                "f1_macro":       round(r["f1_mean"],  4),
            }
            for name, r in results.items()
        }
    }
    path = os.path.join(output_dir, "report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✓ Relatório salvo: {path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    X = [t for t, _ in TRAINING_DATA]
    y = [l for _, l in TRAINING_DATA]

    print(f"\n🎬 CinemaBot — Comparação de Algoritmos NLP")
    print(f"   Exemplos de treino : {len(X)}")
    print(f"   Classes (intenções): {len(set(y))}")
    print(f"   Distribuição       : { {c: y.count(c) for c in sorted(set(y))} }")

    results   = evaluate_all(X, y, cv=5)
    best_name = max(results, key=lambda n: results[n]["acc_mean"])

    print(f"\n🏆 Melhor algoritmo: {best_name.replace(chr(10), ' ')}")
    print(f"   Acurácia: {results[best_name]['acc_mean']:.4f} ± {results[best_name]['acc_std']:.4f}")
    print(f"   F1-macro: {results[best_name]['f1_mean']:.4f}")

    print(f"\n📊 Gerando gráficos em /{args.output}/...")
    plot_accuracy(results, args.output)
    plot_scatter(results, args.output)
    plot_confusion(X, y, results, args.output)
    plot_learning_curves(X, y, results, args.output)
    plot_f1_per_class(X, y, best_name, args.output)
    save_report(results, best_name, args.output)

    print(f"\n✅ Concluído! {len(ALGORITHMS)} algoritmos comparados.")
    print(f"   Arquivos gerados em: ./{args.output}/")

if __name__ == "__main__":
    main()