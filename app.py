from flask import Flask, render_template, request, jsonify
from chatbot import gerar_resposta

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json()
    mensagem = dados.get("mensagem", "").strip()

    if not mensagem:
        return jsonify({"resposta": "Por favor, digite uma mensagem."})

    resposta = gerar_resposta(mensagem)
    return jsonify({"resposta": resposta})


if __name__ == "__main__":
    app.run(debug=True)
