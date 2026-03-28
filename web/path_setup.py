"""
Coloca `repo/src` no sys.path e define MOBA_DRAFT_ROOT.
Assim `moba_draft_agent` importa mesmo sem `pip install -e .` (ex.: IDE ou venv errada).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_web = Path(__file__).resolve().parent
_repo = _web.parent
_src = _repo / "src"
if _src.is_dir():
    p = str(_src.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("MOBA_DRAFT_ROOT", str(_repo.resolve()))
