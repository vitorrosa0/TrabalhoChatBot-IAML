# 🎬 CineBot — Chatbot de Recomendação de Filmes

Projeto desenvolvido para a disciplina de **Inteligência Artificial e Machine Learning (IAML)** da UniAcademia.

---

## ⚙️ Variáveis de Ambiente

Antes de executar o projeto, configure o arquivo `.env` na **raiz do repositório** com as seguintes variáveis:

Os valores das variáveis de ambiente estão no drive, link compartilhado no docs, visto que não é possível subir access tokens no github

| Variável        | Descrição                                                                 | Obrigatória |
|-----------------|---------------------------------------------------------------------------|-------------|
| `HF_TOKEN`      | Token de acesso da Hugging Face (permissão: *Make calls to Inference Providers*) | Sim         |
| `TMDB_API_KEY`  | Chave de API do The Movie Database (TMDB)                                | Sim         |

O arquivo `src/.env.example` serve de template — ele está no repositório e mostra quais variáveis precisam ser configuradas, mas sem valores reais.

```bash
# macOS/Linux
cp src/.env.example .env

# Windows
copy src\.env.example .env
```

Abra o `.env` gerado na raiz e preencha com seus tokens:

```env
HF_TOKEN=seu_token_huggingface_aqui
TMDB_API_KEY=sua_chave_tmdb_aqui
```

> Obtenha o token do Hugging Face em: https://huggingface.co/settings/tokens  
> Obtenha a chave da TMDB em: https://www.themoviedb.org/settings/api

---

## ▶️ Como Executar

### 1. Clone o repositório

```bash
git clone https://github.com/vitorrosa0/TrabalhoChatBot-IAML.git
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

Siga as instruções da seção [Variáveis de Ambiente](#️-variáveis-de-ambiente) acima.

### 5. Execute o chatbot

O CineBot pode ser executado de duas formas a partir da **raiz do repositório**:

#### 🖥️ Modo terminal (CLI)

```bash
python app.py
```

O bot será iniciado diretamente no terminal. Digite sua mensagem e pressione Enter para conversar. Para encerrar, digite `sair`.

#### 🌐 Modo web (interface no navegador)

```bash
python app.py --web
```

O servidor Flask será iniciado e a interface gráfica ficará disponível em `http://localhost:5000`. Abra esse endereço no seu navegador (Chrome recomendado). A interface exibe as mensagens de forma visual, com indicação da fonte de cada resposta (Local, TMDB ou LLM).

---

## 📌 Descrição

O **CineBot** é um chatbot especializado em filmes. O usuário pode perguntar sobre sinopse, diretor, elenco, curiosidades, prêmios e filmes similares em linguagem natural. O sistema utiliza NLP (NLTK) para interpretar as mensagens, classifica a intenção com **Naive Bayes**, consulta a **API do TMDB** para buscar dados de filmes, e usa um **LLM via Hugging Face** (Llama 3.1 8B) para refinar respostas e cobrir perguntas fora do escopo local.

---

## 🧠 Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| Python 3.x | Linguagem principal |
| NLTK + RSLPStemmer | Processamento de Linguagem Natural e stemming |
| Naive Bayes (NLTK) | Classificação de intenções (saudação, afirmação) |
| TMDB API | Repositório principal de dados de filmes |
| Hugging Face (Llama 3.1 8B) | LLM para fallback e refinamento de respostas |
| Flask | Servidor web para a interface gráfica |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## 📁 Estrutura do Projeto

```
TrabalhoChatBot-IAML/
├── app.py                  → Ponto de entrada (CLI e Web)
├── requirements.txt
├── README.md
└── src/
    ├── .env.example            → Template de variáveis de ambiente
    ├── Orchestrator.py         → Coordena NLP, contexto e geração de respostas
    ├── IMovieRepository.py     → Interface e repositório local (dataset.json)
    ├── TMDBRepository.py       → Repositório de filmes via API do TMDB
    ├── StateManagement.py      → Gerenciamento de contexto da conversa
    ├── dataset.json            → Base de dados local de filmes (fallback)
    ├── static/                 → Interface web (HTML/CSS/JS)
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
| "Filmes de ação" | Lista de filmes do gênero via TMDB |
| "Filmografia do Tom Holland" | Filmes do ator via TMDB |

---

## ⚠️ Limitações

- O refinamento de respostas e o fallback dependem de conexão com a API do Hugging Face e de um token válido
- A busca de filmes depende de conexão com a API do TMDB e de uma chave válida
- Gírias ou frases muito informais podem não ser reconhecidas corretamente

---

## 👥 Equipe

- Andrezza Maria
- Gustavo Miranda
- Lucas Ciampi
- João Victor Leal
- Vítor Rosa

---

## 📅 Entrega

**Data:** 15/06/2026 — com apresentação  
**Disciplina:** Inteligência Artificial e Machine Learning — UniAcademia
