# Versão web (Flask). O roadmap sai direto da base validada, sem IA no meio;
# a IA só entra quando o produtor pergunta sobre um ponto.
import json
import os
import re
import unicodedata

from flask import Flask, render_template, request, jsonify, abort, redirect, url_for

import config
from agents import AgenteConhecimento

app = Flask(__name__)
DIR_BASE = os.path.dirname(os.path.abspath(__file__))

# pra adicionar as hortaliças é preciso gerar o JSON dela no mesmo formato e apontar aqui
HORTALICAS = {
    "alface": {
        "nome": "Alface",
        "cientifico": "Lactuca sativa",
        "arquivo": "roadmap_estruturado.json",
        "disponivel": True,
    },
    "couve": {
        "nome": "Couve",
        "cientifico": "Brassica oleracea",
        "arquivo": None,
        "disponivel": False,
    },
    "rucula": {
        "nome": "Rúcula",
        "cientifico": "Eruca sativa",
        "arquivo": None,
        "disponivel": False,
    },
    "tomate": {
        "nome": "Tomate",
        "cientifico": "Solanum lycopersicum",
        "arquivo": None,
        "disponivel": False,
    },
    "cenoura": {
        "nome": "Cenoura",
        "cientifico": "Daucus carota",
        "arquivo": None,
        "disponivel": False,
    },
    "repolho": {
        "nome": "Repolho",
        "cientifico": "Brassica oleracea var. capitata",
        "arquivo": None,
        "disponivel": False,
    },
    "brocolis": {
        "nome": "Brócolis",
        "cientifico": "Brassica oleracea var. italica",
        "arquivo": None,
        "disponivel": False,
    },
    "pimentao": {
        "nome": "Pimentão",
        "cientifico": "Capsicum annuum",
        "arquivo": None,
        "disponivel": False,
    },
    "beterraba": {
        "nome": "Beterraba",
        "cientifico": "Beta vulgaris",
        "arquivo": None,
        "disponivel": False,
    },
    "espinafre": {
        "nome": "Espinafre",
        "cientifico": "Spinacia oleracea",
        "arquivo": None,
        "disponivel": False,
    },
    "pepino": {
        "nome": "Pepino",
        "cientifico": "Cucumis sativus",
        "arquivo": None,
        "disponivel": False,
    },
}

# carrega os embeddings uma vez
agente_conhecimento = AgenteConhecimento()

_roadmaps_carregados = {}


def carregar_roadmap(slug):
    # junta etapas seguidas de mesmo título (a planilha da alface tem duas "COLHEITA" em sequência), tenho que lembrar de mudar depois
    if slug in _roadmaps_carregados:
        return _roadmaps_carregados[slug]

    info = HORTALICAS.get(slug)
    if not info or not info["disponivel"]:
        return None

    with open(os.path.join(DIR_BASE, info["arquivo"]), encoding="utf-8") as f:
        bruto = json.load(f)

    etapas = []
    for etapa in bruto:
        titulo = etapa["titulo"].strip()
        if etapas and etapas[-1]["titulo"].lower() == titulo.lower():
            etapas[-1]["itens"].extend(etapa["itens"])
        else:
            etapas.append({"titulo": titulo, "itens": list(etapa["itens"])})

    for ei, etapa in enumerate(etapas):
        etapa["id"] = f"e{ei}"
        for ii, item in enumerate(etapa["itens"]):
            item["id"] = f"e{ei}-p{ii}"
            item["etapa_idx"] = ei
            item["item_idx"] = ii
            item["slug"] = slugificar(item["titulo"])

    _roadmaps_carregados[slug] = etapas
    return etapas


def slugificar(texto):
    # "Alface Americana" -> "alface-americana"
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def separar_tipos(etapas):
    # a primeira etapa da planilha lista as variedades
    if not etapas:
        return [], []
    return etapas[0]["itens"], etapas[1:]


def conteudo_do_ponto(item, tipo_titulo):
    # conteúdo por variedade (campo opcional "por_tipo")
    especifico = (item.get("por_tipo") or {}).get(tipo_titulo)
    return especifico or item.get("conteudo", "")


@app.route("/")
def inicio():
    return render_template("inicio.html", hortalicas=HORTALICAS)


@app.route("/roadmap/<slug>")
def escolher_tipo(slug):
    info = HORTALICAS.get(slug)
    if not info:
        abort(404)
    etapas = carregar_roadmap(slug)
    if etapas is None:
        return render_template("em_breve.html", hortalica=info), 200

    tipos, _ = separar_tipos(etapas)
    return render_template("tipos.html", slug=slug, hortalica=info, tipos=tipos)


@app.route("/roadmap/<slug>/<tipo_slug>")
def roadmap(slug, tipo_slug):
    info = HORTALICAS.get(slug)
    if not info:
        abort(404)
    etapas = carregar_roadmap(slug)
    if etapas is None:
        return render_template("em_breve.html", hortalica=info), 200

    tipos, demais = separar_tipos(etapas)
    tipo = next((t for t in tipos if t["slug"] == tipo_slug), None)
    if tipo is None:
        return redirect(url_for("escolher_tipo", slug=slug))

    etapas_view = []
    for etapa in demais:
        itens = []
        for item in etapa["itens"]:
            copia = dict(item)
            copia["conteudo"] = conteudo_do_ponto(item, tipo["titulo"])
            itens.append(copia)
        etapas_view.append({**etapa, "itens": itens})

    return render_template(
        "roadmap.html",
        slug=slug,
        hortalica=info,
        tipo=tipo,
        etapas=etapas_view,
    )


@app.route("/api/ajuda", methods=["POST"])
def api_ajuda():
    dados = request.json or {}
    slug = dados.get("hortalica")
    pergunta = (dados.get("pergunta") or "").strip()

    etapas = carregar_roadmap(slug)
    if etapas is None:
        return jsonify({"erro": "hortaliça não encontrada"}), 404
    if not pergunta:
        return jsonify({"erro": "pergunta vazia"}), 400

    try:
        etapa = etapas[int(dados.get("etapa_idx"))]
        item = etapa["itens"][int(dados.get("item_idx"))]
    except (TypeError, ValueError, IndexError):
        return jsonify({"erro": "ponto do roadmap inválido"}), 400

    tipos, _ = separar_tipos(etapas)
    tipo = next((t for t in tipos if t["slug"] == dados.get("tipo")), None)

    resposta = agente_conhecimento.responder_sobre_ponto(
        hortalica=HORTALICAS[slug]["nome"],
        etapa=etapa["titulo"],
        item=item["titulo"],
        conteudo=conteudo_do_ponto(item, tipo["titulo"] if tipo else None),
        pergunta=pergunta,
        tipo=tipo["titulo"] if tipo else None,
        descricao_tipo=tipo.get("conteudo", "") if tipo else "",
    )
    return jsonify({"resposta": resposta})


if __name__ == "__main__":
    app.run(debug=config.DEPURAR, port=config.PORTA)
