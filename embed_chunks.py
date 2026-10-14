# Gera os embeddings dos trechos dos livros de referência (Embrapa, cartilha), roda umaa vez.
# Roda de novo quando os PDFs mudarem.
import json
import os
import time
from google import genai
from google.genai import errors

import config

CHAVE_API = config.CHAVE_GEMINI
if not CHAVE_API:
    raise SystemExit(config.FALTA_CHAVE)

cliente = genai.Client(api_key=CHAVE_API)
MODELO_EMBED = config.MODELO_EMBED

ARQUIVO_SAIDA = "chunks_embeddings.json"
TAM_LOTE = 5
PAUSA_SEG = 6
MAX_TENTATIVAS = 6


def vetorizar_lote(lote):
    espera = 15
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resp = cliente.models.embed_content(model=MODELO_EMBED, contents=lote)
            return [e.values for e in resp.embeddings]
        except errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(f"  limite atingido, aguardando {espera}s antes de tentar de novo "
                      f"(tentativa {tentativa}/{MAX_TENTATIVAS})...")
                time.sleep(espera)
                espera = min(espera * 2, 120)
            else:
                raise
    raise SystemExit("Limite da API continua sendo atingido após várias tentativas. "
                      "Rode o script de novo mais tarde — o progresso já feito foi salvo.")


def main():
    trechos = json.load(open("chunks.json", encoding="utf-8"))

    prontos = []
    if os.path.exists(ARQUIVO_SAIDA):
        prontos = json.load(open(ARQUIVO_SAIDA, encoding="utf-8"))
    inicio = len(prontos)
    if inicio:
        print(f"Retomando: {inicio}/{len(trechos)} trechos já tinham embedding.")

    restantes = trechos[inicio:]
    print(f"Gerando embeddings para {len(restantes)} trechos restantes...")

    for i in range(0, len(restantes), TAM_LOTE):
        lote_trechos = restantes[i:i + TAM_LOTE]
        textos = [c["text"] for c in lote_trechos]
        vetores = vetorizar_lote(textos)
        for c, v in zip(lote_trechos, vetores):
            c["embedding"] = v
        prontos.extend(lote_trechos)

        with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
            json.dump(prontos, f, ensure_ascii=False)
        print(f"  embeddings {len(prontos)}/{len(trechos)}")

        if i + TAM_LOTE < len(restantes):
            time.sleep(PAUSA_SEG)

    print(f"Concluído! Salvo em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
