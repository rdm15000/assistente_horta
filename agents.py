import json
import os
import time
import numpy as np
from google import genai
from google.genai import types, errors

import config

CHAVE_API = config.CHAVE_GEMINI
if not CHAVE_API:
    raise SystemExit(config.FALTA_CHAVE)

cliente = genai.Client(api_key=CHAVE_API)

# se o principal estiver lotado (503), cai pro próximo em vez de ficar esperando
MODELO_CHAT = config.MODELO_CHAT
MODELOS_ALTERNATIVOS = [MODELO_CHAT, "gemini-flash-lite-latest", "gemini-2.5-flash"]
MODELO_EMBED = config.MODELO_EMBED

CAMINHO_ROADMAP = os.path.join(os.path.dirname(__file__), "roadmap_estruturado.json")
CAMINHO_CHUNKS = os.path.join(os.path.dirname(__file__), "chunks_embeddings.json")

ERROS_TEMPORARIOS = ("UNAVAILABLE", "RESOURCE_EXHAUSTED", "503", "429", "DEADLINE_EXCEEDED")


class ModeloIndisponivel(Exception):
    pass


def tentar_gerar(modelo, conteudos, parametros=None, tentativas_por_modelo=2):
    modelos = [modelo] + [m for m in MODELOS_ALTERNATIVOS if m != modelo]
    ultimo_erro = None

    for modelo_atual in modelos:
        espera = 4
        for tentativa in range(1, tentativas_por_modelo + 1):
            try:
                kwargs = {"model": modelo_atual, "contents": conteudos}
                if parametros is not None:
                    kwargs["config"] = parametros
                return cliente.models.generate_content(**kwargs)
            except (errors.ServerError, errors.ClientError) as e:
                ultimo_erro = e
                if any(codigo in str(e) for codigo in ERROS_TEMPORARIOS) and tentativa < tentativas_por_modelo:
                    print(f"  [aviso] {modelo_atual} indisponível, tentando de novo em {espera}s...")
                    time.sleep(espera)
                    espera *= 2
                else:
                    print(f"  [aviso] {modelo_atual} indisponível, tentando modelo alternativo...")
                    break

    raise ModeloIndisponivel(str(ultimo_erro))

REGRAS_LINGUAGEM = """Regras de linguagem (obrigatórias):
- NÃO use advérbios de intensidade vagos: "muito", "pouco", "bastante", "demais",
  "excessivo", "elevado", "intenso", "moderado", "ameno", "extremo". Isso vale
  especialmente para clima ("muito quente", "muito frio", "calor excessivo") e
  para quantidades ("bastante água", "pouco adubo").
- Troque por número e unidade: temperatura em °C, água em mm ou L/m², espaçamento
  em cm, tempo em dias, área em m². Ex.: em vez de "não resiste a climas muito
  quentes", escreva "acima de 30 °C a planta tende a pendoar".
- A referência é o clima brasileiro, não o de regiões extremas. 35 °C no verão do
  Rio e 5 °C no inverno de Curitiba são condições reais do produtor: descreva a
  faixa, não o exagero.
- Se o conteúdo validado e os trechos de referência não trouxerem o número, diga
  explicitamente que a faixa não está especificada na base e sugira confirmar com
  um extensionista local — não preencha com uma palavra de intensidade nem com um
  valor inventado."""


# Agente de Roadmap
# ---------------------------------------------------------------------------
class AgenteRoadmap:
    def __init__(self, caminho=CAMINHO_ROADMAP):
        self.etapas = json.load(open(caminho, encoding="utf-8"))
        self.passos = []
        for etapa in self.etapas:
            for item in etapa["itens"]:
                self.passos.append({
                    "etapa": etapa["titulo"],
                    "titulo": item["titulo"],
                    "conteudo": item["conteudo"],
                    "observacao_especialista": item.get("observacao_especialista", ""),
                })

    def total_passos(self):
        return len(self.passos)

    def passo_atual(self, indice):
        if indice >= len(self.passos):
            return None
        return self.passos[indice]

    def gerar_resposta(self, indice, cidade=None, area_m2=None):
        passo = self.passo_atual(indice)
        if passo is None:
            return "Você concluiu todas as etapas do roadmap de cultivo da alface! 🎉", True

        contexto_local = ""
        if cidade:
            contexto_local = f"O produtor está em {cidade}"
            if area_m2:
                contexto_local += f" e tem {area_m2} m² disponíveis para plantio"
            contexto_local += "."

        prompt = f"""Você é um agente de extensão rural especializado em cultivo de alface.
Sua tarefa é apresentar a etapa atual do roadmap de forma clara e prática para um pequeno produtor.

Etapa do roadmap: {passo['etapa']}
Item: {passo['titulo']}
Conteúdo técnico validado: {passo['conteudo']}
Observação do especialista (aplicar com prioridade): {passo['observacao_especialista']}
{contexto_local}

Escreva a orientação para o produtor em linguagem simples e direta (poucos parágrafos ou lista curta).

{REGRAS_LINGUAGEM}

No fim, pergunte se ele quer seguir para a próxima etapa ou tem alguma dúvida sobre esta etapa."""

        try:
            resp = tentar_gerar(MODELO_CHAT, prompt)
            return resp.text, False
        except ModeloIndisponivel:
          
            texto = f"{passo['etapa']} — {passo['titulo']}\n\n{passo['conteudo']}"
            if passo["observacao_especialista"]:
                texto += f"\n\n(Observação do especialista: {passo['observacao_especialista']})"
            texto += "\n\n[a IA está indisponível no momento, mostrando o conteúdo validado direto da base]"
            texto += "\n\nQuer seguir para a próxima etapa ou tem alguma dúvida?"
            return texto, False


# Agente de Conhecimento 
# ---------------------------------------------------------------------------
class AgenteConhecimento:
    def __init__(self, caminho=CAMINHO_CHUNKS, qtd_trechos=4):
        if not os.path.exists(caminho):
            raise SystemExit(
                "chunks_embeddings.json não encontrado. Rode `python embed_chunks.py` primeiro."
            )
        self.trechos = json.load(open(caminho, encoding="utf-8"))
        self.matriz = np.array([c["embedding"] for c in self.trechos])
        self.qtd_trechos = qtd_trechos

    def _vetorizar(self, consulta):
        espera = 5
        for tentativa in range(1, 6):
            try:
                resp = cliente.models.embed_content(
                    model=MODELO_EMBED,
                    contents=[consulta],
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
                )
                return np.array(resp.embeddings[0].values)
            except (errors.ServerError, errors.ClientError) as e:
                if any(c in str(e) for c in ERROS_TEMPORARIOS) and tentativa < 5:
                    time.sleep(espera)
                    espera = min(espera * 2, 60)
                else:
                    raise

    def _buscar(self, consulta):
        q = self._vetorizar(consulta)
        similaridades = self.matriz @ q / (np.linalg.norm(self.matriz, axis=1) * np.linalg.norm(q) + 1e-8)
        indices = np.argsort(-similaridades)[: self.qtd_trechos]
        return [self.trechos[i] for i in indices]

    def responder(self, pergunta):
        trechos = self._buscar(pergunta)
        contexto = "\n\n".join(f"[Fonte: {t['source']}]\n{t['text']}" for t in trechos)

        prompt = f"""Você é um agente de extensão rural especializado em produção de hortaliças.
Responda a dúvida do produtor usando APENAS as informações do contexto abaixo.
Se o contexto não tiver a resposta, diga que não encontrou essa informação nas referências
e sugira procurar um extensionista local.

Contexto (trechos dos livros de referência):
{contexto}

Pergunta do produtor: {pergunta}

Responda em linguagem simples e direta, citando a fonte entre parênteses quando usar uma informação.

{REGRAS_LINGUAGEM}"""

        try:
            resp = tentar_gerar(MODELO_CHAT, prompt)
            return resp.text
        except ModeloIndisponivel:
            return ("A IA está indisponível no momento (alta demanda no servidor do Gemini). "
                    "Tente de novo em alguns instantes.")

    def responder_sobre_ponto(self, hortalica, etapa, item, conteudo, pergunta,
                              tipo=None, descricao_tipo=""):
        # ancorado primeiro no conteúdo validado do ponto, depois no ageente c
        cultura = tipo or hortalica
        trechos = self._buscar(f"{cultura} - {item}: {pergunta}")
        contexto = "\n\n".join(f"[Fonte: {t['source']}]\n{t['text']}" for t in trechos)

        bloco_tipo = ""
        if tipo:
            bloco_tipo = (
                f"\nVariedade escolhida pelo produtor: {tipo}."
                f"\nCaracterísticas dessa variedade: {descricao_tipo or '(não informadas)'}\n"
            )

        prompt = f"""Você é um agente de extensão rural especializado em produção de hortaliças.
O produtor está consultando o roadmap de cultivo de {hortalica}, no ponto "{item}" (etapa "{etapa}"),
e pediu ajuda sobre esse ponto.
{bloco_tipo}

Conteúdo desse ponto, validado por especialista (use como base principal):
{conteudo or '(sem conteúdo cadastrado)'}

Trechos dos livros de referência (use para complementar):
{contexto}

Pergunta do produtor: {pergunta}

{REGRAS_LINGUAGEM}

Outras regras:
- Responda em linguagem simples e direta, como quem orienta um pequeno produtor.
- Não invente informações; use o conteúdo validado e os trechos acima. Se não houver base
  para responder, diga isso e sugira procurar um extensionista local.
- Cite a fonte entre parênteses quando usar um trecho dos livros.
- Sempre que a recomendação mudar conforme a variedade, responda para a variedade escolhida
  ({cultura}). Se as fontes acima só trouxerem orientação geral para {hortalica}, deixe claro
  que a orientação é geral e não específica dessa variedade."""

        try:
            resp = tentar_gerar(MODELO_CHAT, prompt)
            return resp.text
        except ModeloIndisponivel:
            return ("A IA está indisponível no momento (alta demanda no servidor do Gemini). "
                    "O conteúdo validado do ponto continua disponível acima; tente a IA de novo em instantes.")


# Agente Orquestrador
# ---------------------------------------------------------------------------
class Orquestrador:
    # manda a mensagem pro agente de roadmap (avançar) ou pro de conhecimento

    def classificar(self, mensagem):
        prompt = f"""Classifique a mensagem de um produtor rural em uma destas categorias:
- "avancar": ele quer seguir para a próxima etapa do roadmap (ex: "ok", "próximo", "entendi", "pode continuar")
- "duvida": ele está fazendo uma pergunta específica sobre cultivo (ex: "e se chover muito?", "qual adubo usar?")

Mensagem: "{mensagem}"

Responda APENAS com uma palavra: avancar ou duvida."""

        try:
            resp = tentar_gerar(MODELO_CHAT, prompt)
            texto = resp.text.strip().lower()
            return "avancar" if "avan" in texto else "duvida"
        except ModeloIndisponivel:
         
            m = mensagem.strip().lower()
            palavras_avancar = ("ok", "sim", "proximo", "próximo", "continuar", "entendi", "beleza", "show")
            if m in palavras_avancar or (len(m.split()) <= 3 and "?" not in m):
                return "avancar"
            return "duvida"
