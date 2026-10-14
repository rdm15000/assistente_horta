# Protótipo em terminal (anterior à versão web).
from agents import AgenteRoadmap, AgenteConhecimento, Orquestrador


def main():
    print("=" * 60)
    print("Assistente de Extensão Rural — Cultivo de Alface (protótipo)")
    print("=" * 60)

    cidade = input("Qual sua cidade? ").strip() or None
    area = input("Qual a área disponível para plantio (em m²)? ").strip() or None

    agente_roadmap = AgenteRoadmap()
    agente_conhecimento = AgenteConhecimento()
    orquestrador = Orquestrador()

    indice = 0
    print(f"\nRoadmap com {agente_roadmap.total_passos()} passos. Vamos começar!\n")

    texto, fim = agente_roadmap.gerar_resposta(indice, cidade, area)
    print(f"\n[Assistente]\n{texto}\n")

    while not fim:
        msg = input("[Você] ").strip()
        if msg.lower() in ("sair", "exit", "quit"):
            break

        categoria = orquestrador.classificar(msg)

        if categoria == "avancar":
            indice += 1
            texto, fim = agente_roadmap.gerar_resposta(indice, cidade, area)
            print(f"\n[Assistente]\n{texto}\n")
        else:
            resposta = agente_conhecimento.responder(msg)
            print(f"\n[Assistente]\n{resposta}\n")
            print("(Continue com sua dúvida, ou diga 'próximo' para seguir no agente_roadmap)\n")

    print("Até a próxima!")


if __name__ == "__main__":
    main()
