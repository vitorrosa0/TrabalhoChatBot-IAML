# 🎬 CineBot — Chatbot de Recomendação de Filmes

Projeto desenvolvido para a disciplina de **Inteligência Artificial e Machine Learning (IAML)** da UniAcademia.

---

## 📌 Descrição

O **CineBot** é um chatbot temático com interface web que recomenda filmes com base no gênero informado pelo usuário em linguagem natural. O sistema utiliza técnicas de Processamento de Linguagem Natural (PLN) com a biblioteca **NLTK** para interpretar as mensagens e identificar a intenção e o gênero cinematográfico desejado.

---

## 🧠 Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| Python 3.x | Linguagem principal |
| NLTK | Tokenização, stopwords e processamento de texto |
| simplemma | Lematização em português |
| scikit-learn | Classificador Naive Bayes para detecção de intenções |
| Flask | Servidor web / Backend |
| HTML + CSS + JS | Interface web (Frontend) |

---

## 📁 Estrutura do Projeto

```
TrabalhoChatBot-IAML/
├── app.py              → Servidor Flask (rotas e API)
├── chatbot.py          → Lógica de PLN e geração de respostas
├── filmes.py           → Base de dados de filmes por gênero
├── templates/
│   └── index.html      → Interface web do chatbot
└── README.md
```

---

## 🔬 Pipeline de PLN (chatbot.py)

O módulo `chatbot.py` aplica as seguintes etapas no processamento de cada mensagem:

1. **Lowercase** — converte o texto para minúsculas
2. **Remoção de pontuação** — elimina caracteres especiais
3. **Tokenização** — divide o texto em palavras individuais (usando `word_tokenize` do NLTK)
4. **Remoção de stopwords** — remove palavras sem valor semântico (ex: "o", "de", "que") usando a lista de stopwords em português do NLTK
5. **Lematização** — reduz palavras à sua forma base usando o `simplemma` (ex: "assistindo", "assistiu" → "assistir")

Após o processamento, o sistema:
- **Detecta a intenção** do usuário com um classificador **Naive Bayes (MultinomialNB)** treinado com frases de exemplo, usando `CountVectorizer` do scikit-learn para vetorização
- **Detecta o gênero** cinematográfico mencionado comparando lemas das palavras com o dicionário de palavras-chave

---

## 🎬 Gêneros Disponíveis

- Ação
- Comédia
- Drama
- Terror
- Romance
- Ficção Científica
- Animação
- Suspense

---

## ▶️ Como Executar

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/TrabalhoChatBot-IAML.git
cd TrabalhoChatBot-IAML
```

### 2. Instale as dependências
```bash
pip3 install -r requirements.txt
```

### 3. Execute o servidor
```bash
python3 app.py
```

### 4. Acesse no navegador
```
http://localhost:5000
```

---

## 💬 Exemplos de Uso

| Entrada do Usuário | Resposta do Bot |
|---|---|
| "Oi" | Saudação + explicação dos gêneros disponíveis |
| "Quero um filme de ação" | 3 filmes de ação com título, ano e descrição |
| "Me recomenda uma comédia" | 3 filmes de comédia |
| "Estou com medo, quero terror" | 3 filmes de terror |
| "Sugere ficção científica" | 3 filmes de ficção científica |

---

## ⚠️ Limitações

- O chatbot não possui memória de contexto entre mensagens
- A base de filmes é estática (não consulta APIs externas)
- O entendimento de linguagem natural é baseado em regras e palavras-chave, sem modelos de ML
- Gírias ou frases muito informais podem não ser reconhecidas corretamente

---

## 👥 Equipe

- Andrezza Castro
- Gustavo Miranda
- Lucas Ciampi
- João Victor Leal
- Vítor Rosa

---

## 📅 Entrega

**Data:** 06/04/2026 — com apresentação
**Disciplina:** Inteligência Artificial e Machine Learning — UniAcademia
