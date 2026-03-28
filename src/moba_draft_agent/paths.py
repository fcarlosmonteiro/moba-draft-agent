"""Raiz do repositório (marcador `rules/draft-rules.yaml`)."""

from __future__ import annotations

import os
from pathlib import Path

_MARKER = ("rules", "draft-rules.yaml")


def project_root() -> Path:
    """`MOBA_DRAFT_ROOT` se válido; senão sobe diretórios até achar `rules/draft-rules.yaml`."""
    env = os.environ.get("MOBA_DRAFT_ROOT", "").strip()
    if env:
        root = Path(env).expanduser().resolve()
        if not (root.joinpath(*_MARKER)).is_file():
            msg = f"MOBA_DRAFT_ROOT={root!s} não contém rules/draft-rules.yaml"
            raise FileNotFoundError(msg)
        return root

    here = Path(__file__).resolve().parent
    for p in (here, *here.parents):
        if (p.joinpath(*_MARKER)).is_file():
            return p

    raise RuntimeError(
        "Não foi possível localizar a raiz do projeto (rules/draft-rules.yaml). "
        "Defina MOBA_DRAFT_ROOT ou instale o pacote em modo editável a partir do clone."
    )
