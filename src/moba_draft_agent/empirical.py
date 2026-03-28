"""Consultas aos agregados em data/empirical/*.jsonl (Camada 2)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from moba_draft_agent.champions import ChampionIndex
from moba_draft_agent.paths import project_root


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _canon_champion(name: str, index: ChampionIndex | None) -> str:
    raw = name.strip()
    if not index:
        return raw
    r = index.resolve(raw)
    if r.ok and r.champion:
        return str(r.champion.get("name") or r.champion.get("id") or raw)
    return raw


@dataclass
class EmpiricalStore:
    """Carrega synergies, counters e winrate por rota (uma vez por instância)."""

    root: Path = field(default_factory=project_root)
    _synergy: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _counter: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _winrate: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _loaded: bool = field(default=False, repr=False)

    def _ensure(self) -> None:
        if self._loaded:
            return
        base = self.root / "data" / "empirical"
        self._synergy = _read_jsonl(base / "synergies.jsonl")
        self._counter = _read_jsonl(base / "counters.jsonl")
        self._winrate = _read_jsonl(base / "winrate.jsonl")
        self._loaded = True

    @property
    def synergy_rows(self) -> list[dict[str, Any]]:
        self._ensure()
        return self._synergy

    @property
    def counter_rows(self) -> list[dict[str, Any]]:
        self._ensure()
        return self._counter

    @property
    def winrate_rows(self) -> list[dict[str, Any]]:
        self._ensure()
        return self._winrate


def _sort_pairs(
    items: list[dict[str, Any]], top_k: int
) -> tuple[list[dict[str, Any]], bool]:
    ranked = sorted(
        items,
        key=lambda r: (float(r["winrate"]), int(r["games"])),
        reverse=True,
    )
    truncated = len(ranked) > top_k
    return ranked[:top_k], truncated


def empirical_synergy(
    champion: str,
    min_games: int = 10,
    top_k: int = 8,
    *,
    store: EmpiricalStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """
    Pares de sinergia onde `champion` aparece (mesmo time no ETL).
    Retorno: champion, min_games, pairs[{partner, winrate, games}], truncated.
    """
    c = _canon_champion(champion, champion_index)
    st = store or EmpiricalStore()
    rows: list[dict[str, Any]] = []
    for row in st.synergy_rows:
        c1, c2 = row.get("champion1"), row.get("champion2")
        if c1 == c:
            partner = c2
        elif c2 == c:
            partner = c1
        else:
            continue
        games = int(row.get("games") or 0)
        if games < min_games:
            continue
        rows.append(
            {
                "partner": partner,
                "winrate": float(row["winrate"]),
                "games": games,
            }
        )
    pairs, truncated = _sort_pairs(rows, top_k)
    return {
        "relation": "synergy",
        "champion": c,
        "min_games": min_games,
        "pairs": pairs,
        "truncated": truncated,
    }


def empirical_counter(
    champion: str,
    min_games: int = 10,
    top_k: int = 8,
    *,
    store: EmpiricalStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """
    Métrica de counter do ETL: linhas com champion1 == campeão foco.
    """
    c = _canon_champion(champion, champion_index)
    st = store or EmpiricalStore()
    rows: list[dict[str, Any]] = []
    for row in st.counter_rows:
        if row.get("champion1") != c:
            continue
        games = int(row.get("games") or 0)
        if games < min_games:
            continue
        rows.append(
            {
                "opponent": row.get("champion2"),
                "winrate": float(row["winrate"]),
                "games": games,
            }
        )
    pairs, truncated = _sort_pairs(rows, top_k)
    return {
        "relation": "counter",
        "champion": c,
        "min_games": min_games,
        "pairs": pairs,
        "truncated": truncated,
    }


def empirical_pair(
    champion_a: str,
    champion_b: str,
    relation: Literal["synergy", "counter"],
    *,
    store: EmpiricalStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """Uma linha exata se existir (counter: apenas champion1=a, champion2=b)."""
    a = _canon_champion(champion_a, champion_index)
    b = _canon_champion(champion_b, champion_index)
    st = store or EmpiricalStore()
    if relation == "counter":
        for row in st.counter_rows:
            if row.get("champion1") == a and row.get("champion2") == b:
                return {
                    "found": True,
                    "relation": "counter",
                    "champion1": a,
                    "champion2": b,
                    "winrate": float(row["winrate"]),
                    "games": int(row.get("games") or 0),
                }
        return {"found": False, "relation": "counter", "champion1": a, "champion2": b}

    for row in st.synergy_rows:
        c1, c2 = row.get("champion1"), row.get("champion2")
        if (c1 == a and c2 == b) or (c1 == b and c2 == a):
            return {
                "found": True,
                "relation": "synergy",
                "champion1": c1,
                "champion2": c2,
                "winrate": float(row["winrate"]),
                "games": int(row.get("games") or 0),
            }
    return {"found": False, "relation": "synergy", "champion1": a, "champion2": b}


def empirical_lane_winrate(
    champion: str,
    min_games: int = 10,
    lane: str | None = None,
    *,
    store: EmpiricalStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """Winrate por rota para um campeão; `lane` opcional filtra uma rota."""
    c = _canon_champion(champion, champion_index)
    st = store or EmpiricalStore()
    lane_norm = lane.strip().lower() if lane else None
    rows: list[dict[str, Any]] = []
    for row in st.winrate_rows:
        if row.get("champion") != c:
            continue
        ln = str(row.get("lane") or "")
        if lane_norm and ln.lower() != lane_norm:
            continue
        games = int(row.get("games") or 0)
        if games < min_games:
            continue
        rows.append(
            {
                "lane": ln,
                "winrate": float(row["winrate"]),
                "games": games,
            }
        )
    rows.sort(key=lambda r: (r["games"], r["winrate"]), reverse=True)
    return {
        "champion": c,
        "min_games": min_games,
        "lane_filter": lane,
        "rows": rows,
    }
