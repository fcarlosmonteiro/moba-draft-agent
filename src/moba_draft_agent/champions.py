"""Resolução de nomes de campeão contra o catálogo (Camada 1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from moba_draft_agent.loaders import ProjectConfig, load_catalog


def _norm_variants(key: str) -> list[str]:
    """Inclui chave sem apóstrofo para buscas tipo ksante → K'Sante."""
    out = [key]
    if "'" in key:
        stripped = key.replace("'", "")
        if stripped and stripped != key:
            out.append(stripped)
    return out


def normalize_champion_query(text: str) -> str:
    """
    Normaliza texto para comparação: minúsculas, espaços colapsados,
    apóstrofos tipográficos unificados (ex.: ' vs ').
    """
    s = text.strip().lower()
    for u in ("\u2019", "\u2018", "\u0060"):  # ', ', `
        s = s.replace(u, "'")
    return " ".join(s.split())


@dataclass
class ResolveResult:
    """Resultado de resolve_champion."""

    ok: bool
    """Match único encontrado."""
    ambiguous: bool
    """Vários campeões para a mesma chave normalizada."""
    champion: dict[str, Any] | None
    """Entrada do catálogo quando ok=True."""
    candidates: list[dict[str, Any]] = field(default_factory=list)
    """Candidatos quando ambiguous=True (ou sugestões futuras)."""
    normalized_query: str = ""
    reason: str | None = None
    """empty_query | not_found, etc."""


class ChampionIndex:
    """
    Índice id/name/aliases normalizados → lista de entradas do catálogo.
    Mesmo campeão pode mapear por várias chaves; deduplica por `id` por chave.
    """

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
    """
    Resolve uma string de usuário para uma entrada canônica do catálogo.

    Passe `index` para reutilizar índice em memória; senão usa `catalog` ou
    `config.catalog` ou carrega do disco via `load_catalog()`.
    """
    if index is not None:
        return index.resolve(query)
    if catalog is not None:
        return ChampionIndex.from_catalog(catalog).resolve(query)
    if config is not None:
        return ChampionIndex.from_catalog(config.catalog).resolve(query)
    return ChampionIndex.from_catalog(load_catalog()).resolve(query)
