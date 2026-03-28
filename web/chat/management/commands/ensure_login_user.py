import base64
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


def _repo_root() -> Path:
    return Path(os.environ.get("MOBA_DRAFT_ROOT", ".")).resolve()


def _resolve_password() -> tuple[str | None, str | None]:
    """
    Retorna (password, erro_explicativo).
    Ordem: B64 (evita # cortado no .env) → env → valores crus do arquivo .env.
    """
    b64 = (os.environ.get("DRAFT_WEB_PASSWORD_B64") or "").strip()
    if b64:
        try:
            raw = base64.b64decode(b64, validate=True).decode("utf-8")
            return raw, None
        except (ValueError, UnicodeDecodeError) as e:
            return None, f"DRAFT_WEB_PASSWORD_B64 inválido: {e}"

    pw = os.environ.get("DRAFT_WEB_PASSWORD")
    if pw is not None and pw != "":
        return pw, None

    env_file = _repo_root() / ".env"
    if env_file.is_file():
        try:
            from dotenv import dotenv_values

            v = dotenv_values(env_file).get("DRAFT_WEB_PASSWORD")
            if v is not None and v != "":
                return v, None
        except ImportError:
            pass

    return None, None


def _resolve_username() -> str:
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


class Command(BaseCommand):
    help = "Cria ou atualiza o usuário web (DRAFT_WEB_PASSWORD ou DRAFT_WEB_PASSWORD_B64)."

    def handle(self, *args, **options):
        password, err = _resolve_password()
        if err:
            self.stderr.write(self.style.ERROR(err))
            return
        if not password:
            self.stderr.write(
                self.style.ERROR(
                    "Defina DRAFT_WEB_PASSWORD (aspas se tiver #) ou DRAFT_WEB_PASSWORD_B64. "
                    "Veja web/README.md."
                )
            )
            return

        username = _resolve_username()
        User = get_user_model()
        user, _created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": False, "is_superuser": False},
        )
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Usuário «{username}» pronto para login."))
        self.stdout.write(
            f"  (senha gravada com {len(password)} caracteres — se faltar o #, "
            f"use aspas no .env ou DRAFT_WEB_PASSWORD_B64)"
        )
