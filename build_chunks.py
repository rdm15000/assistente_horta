# Monta o chunks.json: extrai o texto dos PDFs de referência e divide em trechos.
# Só precisa rodar de novo se os PDFs mudarem (e aí rodar o embed_chunks.py depois).
#
# Uso:
#   python build_chunks.py              -> procura os PDFs na pasta "pdfs" do projeto
#   python build_chunks.py CAMINHO      -> procura os PDFs na pasta informada
import json
import os
import sys

from pypdf import PdfReader

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SAIDA = os.path.join(DIR_BASE, "chunks.json")

# (arquivo PDF, nome da fonte que aparece na resposta da IA)
FONTES = [
    ("Ocultivodehortalicas.pdf", "O Cultivo de Hortaliças (EMBRAPA)"),
    ("20210716-cartilha-cultive-sua-horta.pdf", "Cartilha Cultive sua Horta"),
]

TAM_TRECHO = 220    # palavras por trecho
SOBREPOSICAO = 40   # palavras repetidas do trecho anterior


def extrair_palavras(caminho_pdf):
    # texto de todas as páginas, na ordem, já quebrado em palavras
    paginas = [pagina.extract_text() or "" for pagina in PdfReader(caminho_pdf).pages]
    return "\n".join(paginas).split()


def dividir(palavras):
    # janelas de TAM_TRECHO palavras; cada uma começa SOBREPOSICAO palavras
    # antes do fim da anterior, pra não cortar uma orientação no meio
    passo = TAM_TRECHO - SOBREPOSICAO
    trechos = []
    for inicio in range(0, len(palavras), passo):
        trechos.append(" ".join(palavras[inicio:inicio + TAM_TRECHO]))
        if inicio + TAM_TRECHO >= len(palavras):
            break  # essa janela já chegou no fim do texto
    return trechos


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR_BASE, "pdfs")

    saida = []
    for arquivo, fonte in FONTES:
        caminho = os.path.join(pasta, arquivo)
        if not os.path.exists(caminho):
            raise SystemExit(f"Não achei {arquivo} em {pasta}.\n"
                             "Coloque os PDFs nessa pasta ou passe o caminho: "
                             "python build_chunks.py CAMINHO_DA_PASTA")
        trechos = dividir(extrair_palavras(caminho))
        print(f"  {fonte}: {len(trechos)} trechos")
        saida.extend({"source": fonte, "text": t} for t in trechos)

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"Concluído! {len(saida)} trechos salvos em chunks.json")
    print("Se o conteúdo mudou, apague o chunks_embeddings.json e rode o embed_chunks.py.")


if __name__ == "__main__":
    main()
