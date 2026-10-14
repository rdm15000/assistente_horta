# Assistente de Extensão Rural — Hortaliças

Assistente para pequenos produtores de hortaliças, no formato de roadmap 
com apoio de LLM.

O cultivo é apresentado como uma trilha de etapas e pontos. O conteúdo da
trilha vem de uma planilha revisada por uma especialista em olericultura — a
IA não reescreve esse conteúdo. Ela entra só quando o produtor clica num
ponto e faz uma pergunta, e mesmo aí responde ancorada no conteúdo validado
daquele ponto e em trechos de livros de referência (Embrapa, cartilhas).

Na tela, as duas origens são distinguidas por cor: **verde** para o que veio
da planilha validada, **roxo** para o que foi gerado pela IA.

---

## Requisitos

- **Python 3.10 ou mais novo** ([python.org/downloads](https://www.python.org/downloads/))
- Uma **chave da API do Google Gemini** — gratuita, em
  [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Conexão com a internet (a IA roda na nuvem do Google, não na sua máquina)

Não precisa de banco de dados, Docker nem nada além disso.

> **No Windows**, ao instalar o Python, marque a caixa
> **"Add Python to PATH"** na primeira tela do instalador. Sem isso os
> comandos abaixo não funcionam no terminal.

---

## Instalação

### 1. Baixe o projeto

Com git:

```
git clone https://github.com/USUARIO/REPOSITORIO.git
cd REPOSITORIO
```

Sem git: clique em **Code → Download ZIP** no GitHub, extraia, e abra o
terminal dentro da pasta extraída.

### 2. (Recomendado) Crie um ambiente virtual

Isso mantém as bibliotecas deste projeto separadas do resto do seu Python.

**Windows:**
```
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```
python3 -m venv venv
source venv/bin/activate
```

Deu certo se aparecer `(venv)` no começo da linha do terminal. Toda vez que
for rodar o projeto de novo, repita só o comando de ativação.

### 3. Instale as dependências

```
pip install -r requirements.txt
```

Instala Flask (servidor web), google-genai (cliente da API do Gemini), numpy
(busca por similaridade) e openpyxl (leitura da planilha).

### 4. Configure sua chave da API

As configurações ficam num arquivo `config.env`, que **nunca vai para o
GitHub** — assim cada pessoa usa a chave dela. O repositório traz só um
modelo, sem chave nenhuma. Copie o modelo:

**Windows:**
```
copy config.env-example config.env
```

**Linux / macOS:**
```
cp config.env-example config.env
```

Abra o `config.env` num editor de texto e cole sua chave depois do `=`:

```
GEMINI_API_KEY=AIzaSy...sua_chave_aqui
```

Salve o arquivo. As outras configurações têm padrão e podem ficar como estão.

### 5. Rode

```
python app.py
```

Abra **http://localhost:5000** no navegador.

Para parar o servidor, volte ao terminal e aperte **Ctrl + C**.

---

## Usando o site

1. A home lista as hortaliças. Selecione uma. 
2. Escolha a **variedade** (americana, crespa, lisa...). A escolha acompanha
   você no resto da navegação e entra no contexto das respostas da IA.
3. O **roadmap** aparece como uma trilha: etapas em caixas pretas, pontos nas
   caixas brancas dos lados.
4. Clique num ponto para abrir o painel lateral. Em **verde** você vê a
   explicação validada pela especialista; em **roxo**, o campo para perguntar
   à IA sobre aquele ponto (com três sugestões prontas de pergunta).

