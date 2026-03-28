"""Carrega `.env` na raiz do repo antes dos testes (não sobrescreve variáveis já exportadas)."""

from pathlib import Path


def pytest_configure() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env", override=False)
