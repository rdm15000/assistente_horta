import os
from pathlib import Path

DIR_BASE = Path(__file__).resolve().parent
CAMINHO_CONFIG = DIR_BASE / "config.env"


def _carregar_config(caminho):
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and valor and chave not in os.environ:
            os.environ[chave] = valor


_carregar_config(CAMINHO_CONFIG)

FALTA_CHAVE = (
    "GEMINI_API_KEY não configurada.\n"
    "Copie config.env-example para config.env e coloque sua chave do Gemini lá\n"
    "(gere a chave em https://aistudio.google.com/apikey)."
)

CHAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "")

MODELO_CHAT = os.environ.get("CHAT_MODEL", "gemini-flash-latest")
MODELO_EMBED = os.environ.get("EMBED_MODEL", "gemini-embedding-001")

PORTA = int(os.environ.get("PORT", "5000"))
DEPURAR = os.environ.get("FLASK_DEBUG", "1").lower() not in ("0", "false", "no")
