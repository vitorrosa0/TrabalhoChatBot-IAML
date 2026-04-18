from flask import Flask, render_template, request, jsonify, session
from src.core.chatbot import gerar_resposta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json()
    mensagem = dados.get("mensagem", "").strip()
    if not mensagem:
        return jsonify({"resposta": "Por favor, digite uma mensagem."})

    sid = session.get("sid")
    resposta, sid = gerar_resposta(mensagem, sid)
    session["sid"] = sid

    return jsonify({"resposta": resposta})

@app.route("/api/destaques")
def destaques():
    return jsonify(buscar_destaques())

if __name__ == "__main__":
    app.run(debug=True)