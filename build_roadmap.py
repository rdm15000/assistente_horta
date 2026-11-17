# Curadoria do roadmap: lê a planilha e aplica as correções que a especialista deixou na coluna "Observação do Especialista". A planilha não é alterada. Talvez eu altere depois, estou pensando, lol.
#
# 1. conteúdo = só a coluna "Roadmap" (as colunas Gemini e Chat GPT eram
#    comparação de IAs durante a pesquisa, não entram no produto)
# 2. "Retirar"      -> tira o ponto (e a etapa, se ficar vazia)
# 3. "Acrescentar:" -> anexa o resto ao conteúdo
# 4. "Colocar"      -> recado editorial pra mim, não vai pra versão final
# 5. OBS_SUBSTITUI_CONTEUDO -> a observação da planilha vira o conteúdo, pode ser que sai depois
# 6. resto          -> anexa ao fim
#
# Depois disso entra a revisão de nov/2026 (aplicar_revisao_nov_2026), pedida
# pela especialista depois de ver o roadmap pronto. Ela não está na planilha
# "Roadmap Alface.xlsx", que fica como está, de legado:
#
# a. "Adubação" do preparo do solo -> "Adubação de plantio";
#    "Adubação" dos cuidados no cultivo -> "Adubação de cobertura"
# b. o trecho "Análise de solo: ..." sai da adubação de cobertura e vai pra
#    adubação de plantio
# c. a etapa DOENÇAS E PRAGAS deixa de existir: os dois pontos viram um só,
#    "Doenças e pragas comuns na alface", dentro de CUIDADOS NO CULTIVO
# d. com isso a COLHEITA fica sendo a última etapa
# e. sai da adubação de cobertura o parágrafo "Preparo do solo: Como
#    mencionado anteriormente...", que repetia a adubação de plantio
# f. sai do texto de pragas o recado "Colocar lesmas e caracois por último",
#    que estava dentro da célula "Roadmap" e aparecia pro usuário
#
# No fim, o script lista no terminal o que mudou em cada ponto em relação à
# planilha original.


import json
import os
import re

import openpyxl

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
CAMINHO_PLANILHA = os.path.join(DIR_BASE, "Roadmap Alface.xlsx")
NOME_ABA = "Página1"
ARQUIVO_SAIDA = os.path.join(DIR_BASE, "roadmap_estruturado.json")

# o que mudou em cada ponto em relação à planilha original (sai no resumo final)
IGUAL = "Igual à planilha original"
COM_OBS = "Observação da especialista incorporada ao texto"
OBS_NO_LUGAR = "Texto substituído pela observação da especialista"

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


def achar_etapa(etapas, titulo):
    for etapa in etapas:
        if etapa["titulo"].strip().lower() == titulo.lower():
            return etapa
    raise SystemExit(f"Revisão: não achei a etapa '{titulo}' — a planilha mudou?")


def achar_ponto(etapa, titulo):
    for item in etapa["itens"]:
        if item["titulo"].strip().lower() == titulo.lower():
            return item
    raise SystemExit(f"Revisão: não achei o ponto '{titulo}' em '{etapa['titulo']}' — a planilha mudou?")


def aplicar_revisao_nov_2026(etapas, notas):
    preparo = achar_etapa(etapas, "PREPARO DO SOLO")
    cuidados = achar_etapa(etapas, "CUIDADOS NO CULTIVO")
    doencas_pragas = achar_etapa(etapas, "DOENÇAS E PRAGAS")

    # a. nomes das duas adubações
    plantio = achar_ponto(preparo, "Adubação")
    cobertura = achar_ponto(cuidados, "Adubação")
    plantio["titulo"] = "Adubação de plantio"
    cobertura["titulo"] = "Adubação de cobertura"
    notas[id(plantio)] = (
        'Revisão nov/2026: renomeado (antes "Adubação"); recebeu o trecho '
        '"Análise de solo", que estava na adubação de cobertura'
    )
    notas[id(cobertura)] = (
        'Revisão nov/2026: renomeado (antes "Adubação"); saíram o trecho "Análise de solo" '
        '(foi pra adubação de plantio) e o parágrafo "Preparo do solo: Como mencionado anteriormente..."'
    )

    # b. "Análise de solo" muda de adubação (o texto vai inteiro, sem alteração)
    trecho = re.search(r"\s*(Análise de solo:[^\n]*)", cobertura["conteudo"])
    if not trecho:
        raise SystemExit("Revisão: não achei o trecho 'Análise de solo:' na adubação de cobertura.")
    cobertura["conteudo"] = (
        cobertura["conteudo"][: trecho.start()] + cobertura["conteudo"][trecho.end():]
    ).rstrip()
    plantio["conteudo"] = plantio["conteudo"].rstrip() + "\n " + trecho.group(1).strip()

    # e. parágrafo que repetia a adubação de plantio
    cobertura["conteudo"], n = re.subn(
        r"^\s*Preparo do solo: Como mencionado anteriormente[^\n]*\n\s*", "", cobertura["conteudo"]
    )
    if n != 1:
        raise SystemExit("Revisão: não achei o parágrafo 'Preparo do solo: Como mencionado...' na adubação de cobertura.")

    # c. doenças + pragas num ponto só, dentro dos cuidados no cultivo
    doencas = achar_ponto(doencas_pragas, "Doenças Comuns na Alface")
    pragas = achar_ponto(doencas_pragas, "Pragas Comuns na Alface")

    # f. recado editorial que estava no meio do conteúdo
    pragas["conteudo"], n = re.subn(
        r"\s*Colocar lesmas e carac[oó]is por [uú]ltimo\.?\s*$", "", pragas["conteudo"]
    )
    if n != 1:
        raise SystemExit("Revisão: não achei o recado 'Colocar lesmas e caracois por último' no texto de pragas.")
    juntos = {
        "titulo": "Doenças e pragas comuns na alface",
        "conteudo": (
            "DOENÇAS\n \n " + doencas["conteudo"].strip()
            + "\n \n PRAGAS\n \n " + pragas["conteudo"].strip()
        ),
    }
    cuidados["itens"].append(juntos)
    notas[id(juntos)] = (
        'Revisão nov/2026: junta "Doenças Comuns na Alface" e "Pragas Comuns na Alface", que '
        'ficavam na etapa DOENÇAS E PRAGAS (a etapa deixou de existir); saiu o recado '
        '"Colocar lesmas e caracois por último"'
    )

    # d. sem a etapa de doenças e pragas, a colheita passa a ser a última
    etapas.remove(doencas_pragas)
    return etapas


def resumir_mudancas(etapas, notas):
    # Registro do que a curadoria fez em cada ponto. Antes isso ia pra uma
    # planilha de comparação; agora sai aqui, que é onde dá pra conferir sem
    # abrir o Excel.
    print("\nMudanças em relação à planilha original:")
    for etapa in etapas:
        for item in etapa["itens"]:
            nota = notas.get(id(item), "")
            if nota and nota != IGUAL:
                print(f"  {etapa['titulo']} > {item['titulo']}")
                print(f"    {nota}")


def main():
    planilha = openpyxl.load_workbook(CAMINHO_PLANILHA, data_only=True)
    aba = planilha[NOME_ABA]

    linhas = list(aba.iter_rows(values_only=True))
    cabecalho = linhas[0]
    col = {nome: i for i, nome in enumerate(cabecalho) if nome}

    etapas = []
    atual = None
    removidos = []
    notas = {}  # id(ponto) -> o que mudou em relação à planilha original

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

        original = conteudo
        conteudo, manter = aplicar_observacao(descricao, conteudo, obs)

        if not manter:
            removidos.append((atual["titulo"], descricao))
            continue

        ponto = {"titulo": descricao, "conteudo": conteudo}
        atual["itens"].append(ponto)
        if conteudo == original:
            notas[id(ponto)] = IGUAL
        elif conteudo == obs:
            notas[id(ponto)] = OBS_NO_LUGAR
        else:
            notas[id(ponto)] = COM_OBS

    etapas_vazias = [e["titulo"] for e in etapas if not e["itens"]]
    etapas = [e for e in etapas if e["itens"]]
    etapas = aplicar_revisao_nov_2026(etapas, notas)

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(etapas, f, ensure_ascii=False, indent=2)

    total_pontos = sum(len(e["itens"]) for e in etapas)
    print(f"Pontos removidos por indicação da especialista: {len(removidos)}")
    for etapa_titulo, descricao in removidos:
        print(f"  - {etapa_titulo} > {descricao}")
    if etapas_vazias:
        print(f"Etapas que ficaram vazias e saíram: {', '.join(etapas_vazias)}")
    print(f"\nRoadmap final: {len(etapas)} etapas, {total_pontos} pontos.")
    for e in etapas:
        print(f"  {e['titulo']}: {len(e['itens'])} pontos")
    print(f"\nSalvo em {ARQUIVO_SAIDA}")
    resumir_mudancas(etapas, notas)


if __name__ == "__main__":
    main()
