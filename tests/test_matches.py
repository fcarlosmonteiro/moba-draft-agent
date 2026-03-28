from pathlib import Path

import pytest

from moba_draft_agent import (
    ChampionIndex,
    MatchStore,
    load_catalog,
    matches_champion_role_stats,
    matches_composition_stats,
    matches_row_by_gameid,
    matches_sample,
    project_root,
)


@pytest.fixture
def store():
    return MatchStore(root=project_root())


@pytest.fixture
def ch_idx():
    return ChampionIndex.from_catalog(load_catalog())


def test_store_loads_rows(store):
    rows = store.rows
    if not rows:
        pytest.skip("matches.csv ausente")
    assert "gameid" in rows[0]
    assert "result" in rows[0]


def test_row_by_gameid(store):
    r = matches_row_by_gameid("LOLTMNT05_171038", store=store)
    if not store.rows:
        pytest.skip("matches.csv ausente")
    assert r["found"] is True
    assert r["row"]["top_blue"] == "Gnar"
    assert r["row"]["result"] == "0"


def test_composition_blue_gnar_line(store):
    roster = {
        "top": "Gnar",
        "jungle": "Xin Zhao",
        "mid": "Ahri",
        "bottom": "Corki",
        "support": "Leona",
    }
    s = matches_composition_stats("blue", roster, store=store)
    if not store.rows:
        pytest.skip("matches.csv ausente")
    assert s["matches"] >= 1
    assert s["wins_side"] <= s["matches"]


def test_composition_known_winrate_single_game(store):
    r = matches_row_by_gameid("LOLTMNT05_171038", store=store)
    if not r.get("found"):
        pytest.skip("matches.csv ausente")
    row = r["row"]
    roster = {
        "top": row["top_blue"],
        "jungle": row["jng_blue"],
        "mid": row["mid_blue"],
        "bottom": row["bot_blue"],
        "support": row["sup_blue"],
    }
    s = matches_composition_stats("blue", roster, store=store)
    assert s["matches"] >= 1


def test_champion_mid_blue_ahri(store):
    s = matches_champion_role_stats("Ahri", "blue", "mid", store=store)
    if not store.rows:
        pytest.skip("matches.csv ausente")
    assert s["matches"] >= 1
    assert s["column"] == "mid_blue"


def test_champion_alias(store, ch_idx):
    s = matches_champion_role_stats("ksante", "red", "top", store=store, champion_index=ch_idx)
    if not store.rows:
        pytest.skip("matches.csv ausente")
    assert s["champion"] == "K'Sante"


def test_sample_deterministic(store):
    a = matches_sample(limit=3, offset=0, store=store)
    b = matches_sample(limit=3, offset=0, store=store)
    if not store.rows:
        pytest.skip("matches.csv ausente")
    assert a["rows"] == b["rows"]
    assert len(a["rows"]) <= 3


def test_roster_validation(store):
    with pytest.raises(ValueError, match="Faltam papéis"):
        matches_composition_stats("blue", {"top": "Aatrox"}, store=store)


def test_empty_csv(tmp_path: Path):
    root = tmp_path
    md = root / "data" / "matches"
    md.mkdir(parents=True)
    (md / "matches.csv").write_text("gameid,top_blue,jng_blue,mid_blue,bot_blue,sup_blue,top_red,jng_red,mid_red,bot_red,sup_red,result\n", encoding="utf-8")
    st = MatchStore(root=root)
    assert st.rows == []
    s = matches_composition_stats(
        "blue",
        {
            "top": "A",
            "jungle": "B",
            "mid": "C",
            "bottom": "D",
            "support": "E",
        },
        store=st,
    )
    assert s["matches"] == 0
