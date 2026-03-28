"""Consultas a `data/matches/matches.csv`."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from moba_draft_agent.champions import ChampionIndex
from moba_draft_agent.paths import project_root

Side = Literal["blue", "red"]
Role = Literal["top", "jungle", "mid", "bottom", "support"]

ROLE_TO_BLUE: dict[str, str] = {
    "top": "top_blue",
    "jungle": "jng_blue",
    "mid": "mid_blue",
    "bottom": "bot_blue",
    "support": "sup_blue",
}
ROLE_TO_RED: dict[str, str] = {
    "top": "top_red",
    "jungle": "jng_red",
    "mid": "mid_red",
    "bottom": "bot_red",
    "support": "sup_red",
}


def _canon(name: str, index: ChampionIndex | None) -> str:
    raw = name.strip()
    if not index:
        return raw
    r = index.resolve(raw)
    if r.ok and r.champion:
        return str(r.champion.get("name") or r.champion.get("id") or raw)
    return raw


def _side_won(row: dict[str, str], side: Side) -> bool:
    r = row.get("result", "").strip()
    if r == "1":
        return side == "blue"
    if r == "0":
        return side == "red"
    raise ValueError(f"result inválido: {r!r}")


@dataclass
class MatchStore:
    root: Path = field(default_factory=project_root)
    _rows: list[dict[str, str]] | None = field(default=None, repr=False)

    def _path(self) -> Path:
        return self.root / "data" / "matches" / "matches.csv"

    def load(self) -> list[dict[str, str]]:
        if self._rows is not None:
            return self._rows
        path = self._path()
        if not path.is_file():
            self._rows = []
            return self._rows
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self._rows = [dict(row) for row in reader]
        return self._rows

    @property
    def rows(self) -> list[dict[str, str]]:
        return self.load()


def matches_composition_stats(
    side: Side,
    roster: dict[str, str],
    *,
    store: MatchStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """Composição exata de 5; nomes canonicalizados como no CSV."""
    colmap = ROLE_TO_BLUE if side == "blue" else ROLE_TO_RED
    missing = set(colmap.keys()) - set(roster.keys())
    if missing:
        raise ValueError(f"Faltam papéis no roster: {sorted(missing)}")
    extra = set(roster.keys()) - set(colmap.keys())
    if extra:
        raise ValueError(f"Papéis desconhecidos: {sorted(extra)}")

    expected = {colmap[role]: _canon(roster[role], champion_index) for role in colmap}

    st = store or MatchStore()
    games = 0
    wins = 0
    for row in st.rows:
        if all(row.get(col, "").strip() == champ for col, champ in expected.items()):
            games += 1
            if _side_won(row, side):
                wins += 1

    return {
        "side": side,
        "roster": roster,
        "matches": games,
        "wins_side": wins,
        "winrate_side": (wins / games) if games else None,
    }


def matches_champion_role_stats(
    champion: str,
    side: Side,
    role: str,
    *,
    store: MatchStore | None = None,
    champion_index: ChampionIndex | None = None,
) -> dict[str, Any]:
    """Contagem e vitórias do lado escolhido quando o campeão está na coluna da rota."""
    role_l = role.strip().lower()
    if role_l == "bot":
        role_l = "bottom"
    colmap = ROLE_TO_BLUE if side == "blue" else ROLE_TO_RED
    if role_l not in colmap:
        raise ValueError(f"Papel inválido: {role!r}; use {sorted(colmap)}")

    col = colmap[role_l]
    c = _canon(champion, champion_index)
    st = store or MatchStore()
    games = 0
    wins = 0
    for row in st.rows:
        if row.get(col, "").strip() != c:
            continue
        games += 1
        if _side_won(row, side):
            wins += 1

    return {
        "champion": c,
        "side": side,
        "role": role_l,
        "column": col,
        "matches": games,
        "wins_side": wins,
        "winrate_side": (wins / games) if games else None,
    }


def matches_sample(
    limit: int = 10,
    offset: int = 0,
    *,
    store: MatchStore | None = None,
) -> dict[str, Any]:
    """Fatia ordenada por `gameid` (reprodutível)."""
    st = store or MatchStore()
    rows = st.rows
    sorted_rows = sorted(rows, key=lambda r: r.get("gameid", ""))
    slice_rows = sorted_rows[offset : offset + limit]
    return {
        "limit": limit,
        "offset": offset,
        "count": len(slice_rows),
        "total_rows": len(rows),
        "rows": slice_rows,
    }


def matches_row_by_gameid(
    gameid: str,
    *,
    store: MatchStore | None = None,
) -> dict[str, Any]:
    st = store or MatchStore()
    gid = gameid.strip()
    for row in st.rows:
        if row.get("gameid", "").strip() == gid:
            return {"found": True, "row": row}
    return {"found": False, "gameid": gid}
