"""Carrega arquivos da Camada 1 (regras, catálogo, políticas)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from moba_draft_agent.paths import project_root


def load_draft_rules(root: Path | None = None) -> dict[str, Any]:
    path = (root or project_root()) / "rules" / "draft-rules.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("draft-rules.yaml deve ser um mapping na raiz")
    return data


def load_catalog(root: Path | None = None) -> dict[str, Any]:
    path = (root or project_root()) / "catalog" / "champions.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("champions.yaml deve ser um mapping na raiz")
    return data


def load_policies(root: Path | None = None) -> str:
    path = (root or project_root()) / "policies" / "assistant.md"
    return path.read_text(encoding="utf-8")


@dataclass
class ProjectConfig:
    """
    Acesso com cache em memória aos artefatos da Camada 1.
    Útil para reutilizar o mesmo processo sem reler disco a cada tool.
    """

    root: Path = field(default_factory=project_root)
    _draft_rules: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _catalog: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _policies: str | None = field(default=None, init=False, repr=False)

    @property
    def draft_rules(self) -> dict[str, Any]:
        if self._draft_rules is None:
            self._draft_rules = load_draft_rules(self.root)
        return self._draft_rules

    @property
    def catalog(self) -> dict[str, Any]:
        if self._catalog is None:
            self._catalog = load_catalog(self.root)
        return self._catalog

    @property
    def policies(self) -> str:
        if self._policies is None:
            self._policies = load_policies(self.root)
        return self._policies

    def clear_cache(self) -> None:
        self._draft_rules = None
        self._catalog = None
        self._policies = None
