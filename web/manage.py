#!/usr/bin/env python
"""Django CLI — raiz do repositório = um nível acima de `web/`."""

import os
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    try:
        from dotenv import load_dotenv

        load_dotenv(repo_root / ".env", override=False)
    except ImportError:
        pass
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.setdefault("MOBA_DRAFT_ROOT", str(repo_root))
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django não instalado. Rode: pip install -e \".[web]\""
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
