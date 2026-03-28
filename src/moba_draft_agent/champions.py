"""Nome digitado → entrada do catálogo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from moba_draft_agent.loaders import ProjectConfig, load_catalog


def _norm_variants(key: str) -> list[str]:
    """Também indexa variante sem `'` (ex.: ksante → K'Sante)."""
    out = [key]
    if "'" in key:
        stripped = key.replace("'", "")
        if stripped and stripped != key:
            out.append(stripped)
    return out


def normalize_champion_query(text: str) -> str:
    """Minúsculas, espaços únicos, apóstrofos tipográficos → ASCII."""
    s = text.strip().lower()
    for u in ("\u2019", "\u2018", "\u0060"):
        s = s.replace(u, "'")
    return " ".join(s.split())


@dataclass
class ResolveResult:
    ok: bool
    ambiguous: bool
    champion: dict[str, Any] | None
    candidates: list[dict[str, Any]] = field(default_factory=list)
    normalized_query: str = ""
    reason: str | None = None


class ChampionIndex:
    def __init__(self, champions: list[dict[str, Any]]) -> None:
        self._champions = champions
        self._by_norm: dict[str, list[dict[str, Any]]] = {}
        for c in champions:
            keys: set[str] = set()
            for raw in (c.get("id"), c.get("name")):
                if raw is not None and str(raw).strip():
                    keys.add(normalize_champion_query(str(raw)))
            for a in c.get("aliases") or []:
                if str(a).strip():
                    keys.add(normalize_champion_query(str(a)))
            for key in keys:
                for variant in _norm_variants(key):
                    bucket = self._by_norm.setdefault(variant, [])
                    if not any(x.get("id") == c.get("id") for x in bucket):
                        bucket.append(c)

    @classmethod
    def from_catalog(cls, catalog: dict[str, Any]) -> ChampionIndex:
        ch = catalog.get("champions")
        if not isinstance(ch, list):
            raise ValueError("catalog['champions'] deve ser uma lista")
        return cls(ch)

    def resolve(self, query: str) -> ResolveResult:
        n = normalize_champion_query(query)
        if not n:
            return ResolveResult(
                ok=False,
                ambiguous=False,
                champion=None,
                candidates=[],
                normalized_query=n,
                reason="empty_query",
            )

        found = self._by_norm.get(n, [])
        if len(found) == 1:
            return ResolveResult(
                ok=True,
                ambiguous=False,
                champion=found[0],
                candidates=[],
                normalized_query=n,
            )
        if len(found) > 1:
            return ResolveResult(
                ok=False,
                ambiguous=True,
                champion=None,
                candidates=found,
                normalized_query=n,
                reason="ambiguous",
            )

        return ResolveResult(
            ok=False,
            ambiguous=False,
            champion=None,
            candidates=[],
            normalized_query=n,
            reason="not_found",
        )


def resolve_champion(
    query: str,
    *,
    catalog: dict[str, Any] | None = None,
    index: ChampionIndex | None = None,
    config: ProjectConfig | None = None,
) -> ResolveResult:
    """Prioridade: `index` → `catalog` → `config.catalog` → disco."""
    if index is not None:
        return index.resolve(query)
    if catalog is not None:
        return ChampionIndex.from_catalog(catalog).resolve(query)
    if config is not None:
        return ChampionIndex.from_catalog(config.catalog).resolve(query)
    return ChampionIndex.from_catalog(load_catalog()).resolve(query)
