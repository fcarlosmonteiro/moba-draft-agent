"""Credenciais do MVP: só variáveis de ambiente (Render / .env). Sem banco."""

from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path

SESSION_AUTH_KEY = "draft_web_ok"


def _repo_root() -> Path:
    env = (os.environ.get("MOBA_DRAFT_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # web/chat/auth_env.py → raiz do repo (sem depender do cwd)
    return Path(__file__).resolve().parents[2]


def _refresh_env_from_dotenv() -> None:
    path = _repo_root() / ".env"
    if not path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=True)
    except ImportError:
        pass


def resolve_web_password() -> str | None:
    _refresh_env_from_dotenv()
    b64 = (os.environ.get("DRAFT_WEB_PASSWORD_B64") or "").strip()
    if b64:
        try:
            return base64.b64decode(b64, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    pw = os.environ.get("DRAFT_WEB_PASSWORD")
    if pw is not None and pw != "":
        return pw

    env_file = _repo_root() / ".env"
    if env_file.is_file():
        try:
            from dotenv import dotenv_values

            v = dotenv_values(env_file).get("DRAFT_WEB_PASSWORD")
            if v is not None and v != "":
                return v
        except ImportError:
            pass
    return None


def resolve_web_user() -> str:
    _refresh_env_from_dotenv()
    u = os.environ.get("DRAFT_WEB_USER", "").strip()
    if u:
        return u
    env_file = _repo_root() / ".env"
    if env_file.is_file():
        try:
            from dotenv import dotenv_values

            v = dotenv_values(env_file).get("DRAFT_WEB_USER")
            if v and str(v).strip():
                return str(v).strip()
        except ImportError:
            pass
    return "admin"


def credentials_match(username: str, password: str) -> bool:
    expected_p = resolve_web_password()
    if not expected_p:
        return False
    expected_u = resolve_web_user()
    if username.strip() != expected_u:
        return False
    return secrets.compare_digest(
        password.encode("utf-8"),
        expected_p.encode("utf-8"),
    )
