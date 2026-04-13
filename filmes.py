# Base de dados de filmes por gênero

FILMES = {
    "acao": [
        {"titulo": "Mad Max: Estrada da Fúria", "ano": 2015, "descricao": "Uma mulher rebelde e um fugitivo cruzam um mundo pós-apocalíptico em busca de liberdade."},
        {"titulo": "John Wick", "ano": 2014, "descricao": "Um ex-assassino volta à ativa para se vingar da morte de seu cachorro."},
        {"titulo": "Top Gun: Maverick", "ano": 2022, "descricao": "Maverick volta a treinar jovens pilotos de elite para uma missão impossível."},
        {"titulo": "Missão Impossível: Acerto de Contas", "ano": 2023, "descricao": "Ethan Hunt enfrenta sua missão mais perigosa para salvar o mundo."},
        {"titulo": "Os Vingadores", "ano": 2012, "descricao": "Heróis da Marvel se unem para salvar a Terra de Loki e seu exército alienígena."},
    ],
    "comedia": [
        {"titulo": "Se Beber, Não Case!", "ano": 2009, "descricao": "Quatro amigos acoram em Las Vegas e precisam descobrir o que aconteceu na noite anterior."},
        {"titulo": "Todo Mundo em Pânico", "ano": 2000, "descricao": "Uma paródia hilária dos filmes de terror dos anos 90."},
        {"titulo": "Superbad", "ano": 2007, "descricao": "Dois amigos tentam aproveitar ao máximo o último ano do ensino médio."},
        {"titulo": "A Grande Viagem", "ano": 2006, "descricao": "Um grupo de idosos foge do asilo para ver um jogo de futebol americano."},
        {"titulo": "Debi e Loide: Dois Idiotas em Apuros", "ano": 1994, "descricao": "Um motorista e seu amigo embarcam em uma divertida viagem por Aspen para devolver uma maleta ao proprietário."},
    ],
    "drama": [
        {"titulo": "O Poderoso Chefão", "ano": 1972, "descricao": "A saga da família Corleone, uma das mais poderosas da máfia americana."},
        {"titulo": "Clube da Luta", "ano": 1999, "descricao": "Um homem insatisfeito com a vida cria um clube clandestino de lutas."},
        {"titulo": "Forrest Gump", "ano": 1994, "descricao": "A história de um homem simples que, sem querer, participa de eventos históricos dos EUA."},
        {"titulo": "À Espera de um Milagre", "ano": 1999, "descricao": "Um guarda de prisão convive com um presidiário que possui poderes misteriosos."},
        {"titulo": "Interestelar", "ano": 2014, "descricao": "Astronautas viajam por um buraco de minhoca em busca de um novo lar para a humanidade."},
    ],
    "terror": [
        {"titulo": "O Iluminado", "ano": 1980, "descricao": "Um escritor leva a família para um hotel isolado e começa a enlouquecer."},
        {"titulo": "Hereditário", "ano": 2018, "descricao": "Após a morte da matriarca, uma família começa a revelar segredos sombrios."},
        {"titulo": "It: A Coisa", "ano": 2017, "descricao": "Um grupo de crianças enfrenta uma entidade maligna que se disfarça de palhaço."},
        {"titulo": "A Bruxa", "ano": 2015, "descricao": "Uma família puritana é aterrorizada por forças sobrenaturais na Nova Inglaterra do século XVII."},
        {"titulo": "Get Out", "ano": 2017, "descricao": "Um homem negro visita a família da namorada e descobre algo perturbador."},
    ],
    "romance": [
        {"titulo": "Titanic", "ano": 1997, "descricao": "Um amor improvável nasce entre duas pessoas de classes sociais opostas no navio mais famoso da história."},
        {"titulo": "Diário de uma Paixão", "ano": 2004, "descricao": "Um casal de jovens vive um romance intenso nos anos 40 nos EUA."},
        {"titulo": "La La Land", "ano": 2016, "descricao": "Um pianista e uma aspirante a atriz se apaixonam em Los Angeles e perseguem seus sonhos."},
        {"titulo": "Simplesmente Amor", "ano": 2003, "descricao": "Várias histórias de amor se entrelaçam em Londres durante o Natal."},
        {"titulo": "Teoria de Tudo", "ano": 2014, "descricao": "A história de amor entre Stephen Hawking e sua primeira esposa Jane."},
    ],
    "ficcao_cientifica": [
        {"titulo": "Matrix", "ano": 1999, "descricao": "Um hacker descobre que o mundo em que vive é uma simulação controlada por máquinas."},
        {"titulo": "Duna", "ano": 2021, "descricao": "Um jovem nobre assume o destino de um planeta desértico com o recurso mais valioso do universo."},
        {"titulo": "Blade Runner 2049", "ano": 2017, "descricao": "Um caçador de replicantes descobre um segredo que pode mudar o futuro da humanidade."},
        {"titulo": "Arrival", "ano": 2016, "descricao": "Uma linguista tenta se comunicar com alienígenas que chegam à Terra."},
        {"titulo": "Ex Machina", "ano": 2014, "descricao": "Um programador é escolhido para avaliar a inteligência de uma robô com aparência humana."},
    ],
    "animacao": [
        {"titulo": "Homem-Aranha no Aranhaverso", "ano": 2018, "descricao": "Miles Morales se torna o Homem-Aranha e conhece versões alternativas do herói."},
        {"titulo": "Viva: A Vida é uma Festa", "ano": 2017, "descricao": "Um garoto mexicano visita o mundo dos mortos em busca de seu bisavô músico."},
        {"titulo": "Soul", "ano": 2020, "descricao": "Um músico de jazz tem sua alma separada do corpo e precisa voltar à vida."},
        {"titulo": "O Rei Leão", "ano": 1994, "descricao": "Um leão é exilado após ser acusado da morte do pai e precisa reconquistar seu reino."},
        {"titulo": "Spirited Away", "ano": 2001, "descricao": "Uma garota entra em um mundo espiritual e precisa trabalhar para salvar seus pais."},
    ],
    "suspense": [
        {"titulo": "Parasita", "ano": 2019, "descricao": "Uma família pobre se infiltra na vida de uma família rica com consequências imprevisíveis."},
        {"titulo": "Whiplash", "ano": 2014, "descricao": "Um jovem baterista é submetido a um treinamento extremo por um professor obsessivo."},
        {"titulo": "Zodíaco", "ano": 2007, "descricao": "Um cartunista de jornal fica obcecado em descobrir a identidade do assassino Zodíaco."},
        {"titulo": "Oldboy", "ano": 2003, "descricao": "Um homem é libertado após 15 anos preso sem saber o motivo e busca vingança."},
        {"titulo": "Primal Fear", "ano": 1996, "descricao": "Um advogado defende um jovem acusado de assassinato e descobre camadas de manipulação."},
    ],
}

MAPA_GENEROS = {
    "acao": ["ação", "acao", "aventura", "luta", "heroi", "herói", "explosao", "explosão", "adrenalina", "combate"],
    "comedia": ["comedia", "comédia", "engraçado", "engracado", "rir", "humor", "divertido", "risada", "piada"],
    "drama": ["drama", "emocionante", "emoção", "emocao", "reflexao", "reflexão", "profundo", "intenso", "serio", "sério"],
    "terror": ["terror", "medo", "assustador", "horror", "susto", "assombrado", "sobrenatural", "sinistro"],
    "romance": ["romance", "amor", "romantico", "romântico", "casal", "paixao", "paixão", "apaixonado", "sentimento"],
    "ficcao_cientifica": ["ficção", "ficcao", "científica", "cientifica", "sci-fi", "scifi", "nave", "aliens", "alienigena", "futuro", "tecnologia", "robo", "robô", "espaco", "espaço"],
    "animacao": ["animação", "animacao", "desenho", "infantil", "pixar", "disney"],
    "suspense": ["suspense", "thriller", "misterio", "mistério", "tensão", "tensao", "policial", "investigação", "investigacao", "crime"],
}