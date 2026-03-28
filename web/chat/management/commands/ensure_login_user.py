import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria ou atualiza o usuário web (DRAFT_WEB_USER + DRAFT_WEB_PASSWORD)."

    def handle(self, *args, **options):
        password = os.environ.get("DRAFT_WEB_PASSWORD")
        if not password:
            self.stderr.write(
                self.style.ERROR("Defina DRAFT_WEB_PASSWORD no ambiente (Release no Render).")
            )
            return
        username = os.environ.get("DRAFT_WEB_USER", "admin").strip() or "admin"
        User = get_user_model()
        user, _created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": False, "is_superuser": False},
        )
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Usuário «{username}» pronto para login."))
