# 🎬 CineBot — Chatbot de Recomendação de Filmes

Projeto desenvolvido para a disciplina de **Inteligência Artificial e Machine Learning (IAML)** da UniAcademia.

---

## 📌 Descrição

O **CineBot** é um chatbot de linha de comando especializado em filmes. O usuário pode perguntar sobre sinopse, diretor, elenco, curiosidades, prêmios e filmes similares em linguagem natural. O sistema utiliza NLP (NLTK) para interpretar as mensagens, classifica a intenção com **Naive Bayes**, e usa um LLM (Llama 3.1 via Hugging Face) para refinar as respostas e cobrir perguntas fora do escopo local.

---

## 🧠 Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| Python 3.x | Linguagem principal |
| NLTK + RSLPStemmer | Processamento de Linguagem Natural e stemming |
| Naive Bayes (NLTK) | Classificação de intenções (saudação, afirmação) |
| Hugging Face (Llama 3.1 8B) | LLM para fallback e refinamento de respostas |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## 📁 Estrutura do Projeto

```
TrabalhoChatBot-IAML/
├── requirements.txt
├── README.md
└── src/
    ├── app.py                  → Ponto de entrada (CLI)
    ├── Orchestrator.py         → Coordena NLP, contexto e geração de respostas
    ├── IMovieRepository.py     → Repositório de filmes (leitura do dataset.json)
    ├── StateManagement.py      → Gerenciamento de contexto da conversa
    ├── dataset.json            → Base de dados de filmes
    ├── entities/               → Modelos de dados (Movie, Director, Actor)
    ├── nlp/                    → Pipeline de NLP e classificadores de intenção
    └── learningModel/          → Integração com LLM (HuggingFaceFallback)
```

---

## 🔬 Pipeline de NLP

Cada mensagem do usuário passa pelas seguintes etapas (em `nlp/NLPProcessor.py`):

1. **Lowercase** — converte o texto para minúsculas
2. **Remoção de acentos** — normalização Unicode
3. **Remoção de pontuação** — elimina caracteres especiais
4. **Tokenização** — divide o texto em palavras individuais
5. **Stemming** — reduz palavras à raiz morfológica com `RSLPStemmer` (ex: "dirigiu", "diretor" → mesmo stem)

Após o processamento:
- **Classificação de intenção** via regras com stems + **Naive Bayes** para saudações e afirmações
- **Extração de entidade** — identifica o filme mencionado na mensagem
- **Geração de resposta** local baseada na intenção e no contexto da conversa
- **Refinamento** via LLM (Hugging Face) para tornar a resposta mais natural

---

## 🎬 Filmes Disponíveis no Dataset

- Interestelar (2014)
- O Poderoso Chefão (1972)

---

## ▶️ Como Executar

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/TrabalhoChatBot-IAML.git
cd TrabalhoChatBot-IAML
```

### 2. Crie e ative um ambiente virtual (recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

O arquivo `src/.env.example` serve de template, ele está no repositório e mostra quais variáveis precisam ser configuradas, mas sem valores reais.

Para configurar, copie o template e preencha com o seu token:
```bash
# macOS/Linux
cp src/.env.example src/.env

# Windows
copy src\.env.example src\.env
```

Abra o `src/.env` gerado e substitua `seu_token_aqui` pelo seu token pessoal do Hugging Face.

> Obtenha o token (com permissão "Make calls to Inference Providers") em: https://huggingface.co/settings/tokens

### 5. Execute o chatbot
```bash
cd src
python3 app.py
```

---

## 💬 Exemplos de Uso

| Entrada do Usuário | Resposta do Bot |
|---|---|
| "Oi" | Saudação e apresentação do CineBot |
| "Me fala sobre Interestelar" | Inicia contexto com o filme |
| "Qual a sinopse?" | Sinopse do filme em contexto |
| "Quem dirigiu?" | Nome e estilo do diretor |
| "Me conta uma curiosidade" | Curiosidade de bastidores |
| "Quais prêmios ele ganhou?" | Oscars e indicações |
| "Tem algum filme parecido?" | Lista de filmes similares |

---

## ⚠️ Limitações

- O dataset é local e contém apenas 2 filmes (Interestelar e O Poderoso Chefão)
- O refinamento de respostas e o fallback dependem de conexão com a API do Hugging Face e de um token válido
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
