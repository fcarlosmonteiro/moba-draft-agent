import path_setup  # noqa: F401 — src/ no path antes do Django

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_root / ".env", override=True)
except ImportError:
    pass

os.environ.setdefault("MOBA_DRAFT_ROOT", str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
