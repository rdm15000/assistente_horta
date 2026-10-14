# Curadoria do roadmap: lê a planilha e aplica as correções que a especialista deixou na coluna "Observação do Especialista". A planilha não é alterada. Talvez eu altere depois, estou pensando, lol.
#
# 1. conteúdo = só a coluna "Roadmap" (as colunas Gemini e Chat GPT eram
#    comparação de IAs durante a pesquisa, não entram no produto)
# 2. "Retirar"      -> tira o ponto (e a etapa, se ficar vazia)
# 3. "Acrescentar:" -> anexa o resto ao conteúdo
# 4. "Colocar"      -> recado editorial pra mim, não vai pra versão final
# 5. OBS_SUBSTITUI_CONTEUDO -> a observação da planilha vira o conteúdo, pode ser que sai depois
# 6. resto          -> anexa ao fim


import json
import os
import re

import openpyxl

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
CAMINHO_PLANILHA = os.path.join(DIR_BASE, "Roadmap Alface.xlsx")
NOME_ABA = "Página1"
ARQUIVO_SAIDA = os.path.join(DIR_BASE, "roadmap_estruturado.json")

OBS_SUBSTITUI_CONTEUDO = {
    "cuidados após o transplantio",
}

def texto(valor):
    return str(valor).strip() if valor is not None else ""


def eh_cabecalho_de_etapa(nivel):
    # etapa = nível inteiro (1, 2, 3...); ponto = subnível, que o Excel
    # converteu em data/string
    return isinstance(nivel, float) and nivel == int(nivel)


def juntar(conteudo, extra):
    conteudo = conteudo.rstrip()
    extra = extra.strip()
    if not conteudo:
        return extra
    if not extra:
        return conteudo
    if conteudo[-1] not in ".!?:;":
        conteudo += "."
    return f"{conteudo} {extra}"


def aplicar_observacao(titulo, conteudo, obs):
    # devolve (conteudo, manter); manter=False = a especialista mandou tirar
    if not obs:
        return conteudo, True

    obs_lower = obs.lower()

    if obs_lower.startswith("retirar"):
        return conteudo, False

    if obs_lower.startswith("acrescentar"):
        complemento = re.sub(r"^acrescentar\s*:?\s*", "", obs, flags=re.IGNORECASE)
        return juntar(conteudo, complemento), True

    if obs_lower.startswith("colocar"):
        return conteudo, True

    if titulo.strip().lower() in OBS_SUBSTITUI_CONTEUDO:
        return obs, True

    return juntar(conteudo, obs), True


def main():
    planilha = openpyxl.load_workbook(CAMINHO_PLANILHA, data_only=True)
    aba = planilha[NOME_ABA]

    linhas = list(aba.iter_rows(values_only=True))
    cabecalho = linhas[0]
    col = {nome: i for i, nome in enumerate(cabecalho) if nome}

    etapas = []
    atual = None
    removidos = []

    for linha in linhas[1:]:
        if all(c in (None, "") for c in linha):
            continue

        nivel = linha[col["NIVEL"]]
        descricao = texto(linha[col["DESCRIÇÃO"]])
        if not descricao:
            continue

        if eh_cabecalho_de_etapa(nivel):
            atual = {"titulo": descricao, "itens": []}
            etapas.append(atual)
            continue

        if atual is None:
            continue

        conteudo = texto(linha[col["Roadmap"]])
        obs = texto(linha[col["Observação do Especialista"]])

        conteudo, manter = aplicar_observacao(descricao, conteudo, obs)

        if not manter:
            removidos.append(f"{atual['titulo']} > {descricao}")
            continue

        atual["itens"].append({"titulo": descricao, "conteudo": conteudo})

    etapas_vazias = [e["titulo"] for e in etapas if not e["itens"]]
    etapas = [e for e in etapas if e["itens"]]

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(etapas, f, ensure_ascii=False, indent=2)

    total_pontos = sum(len(e["itens"]) for e in etapas)
    print(f"Pontos removidos por indicação da especialista: {len(removidos)}")
    for r in removidos:
        print(f"  - {r}")
    if etapas_vazias:
        print(f"Etapas que ficaram vazias e saíram: {', '.join(etapas_vazias)}")
    print(f"\nRoadmap final: {len(etapas)} etapas, {total_pontos} pontos.")
    for e in etapas:
        print(f"  {e['titulo']}: {len(e['itens'])} pontos")
    print(f"\nSalvo em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
