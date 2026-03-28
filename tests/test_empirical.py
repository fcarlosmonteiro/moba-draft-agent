"""Fase 4 — dados empíricos JSONL."""

from pathlib import Path

import pytest

from moba_draft_agent import (
    ChampionIndex,
    EmpiricalStore,
    empirical_counter,
    empirical_lane_winrate,
    empirical_pair,
    empirical_synergy,
    load_catalog,
    project_root,
)


@pytest.fixture
def store():
    return EmpiricalStore(root=project_root())


@pytest.fixture
def ch_idx():
    return ChampionIndex.from_catalog(load_catalog())


def test_synergy_aatrox_has_pairs(store):
    r = empirical_synergy("Aatrox", min_games=10, top_k=5, store=store)
    assert r["relation"] == "synergy"
    assert r["champion"] == "Aatrox"
    assert len(r["pairs"]) <= 5
    assert all(p["games"] >= 10 for p in r["pairs"])
    assert all("partner" in p for p in r["pairs"])


def test_counter_directional(store):
    r = empirical_counter("Aatrox", min_games=5, top_k=3, store=store)
    assert r["relation"] == "counter"
    assert len(r["pairs"]) <= 3


def test_pair_synergy_found(store):
    r = empirical_pair("Aatrox", "Alistar", "synergy", store=store)
    assert r["found"] is True
    assert r["games"] >= 1


def test_pair_counter_found(store):
    r = empirical_pair("Aatrox", "Ahri", "counter", store=store)
    assert r["found"] is True


def test_lane_winrate_aatrox(store):
    r = empirical_lane_winrate("Aatrox", min_games=50, store=store)
    assert r["champion"] == "Aatrox"
    assert len(r["rows"]) >= 1
    for row in r["rows"]:
        assert row["games"] >= 50


def test_lane_filter_mid(store):
    r = empirical_lane_winrate("Ahri", min_games=1, lane="mid", store=store)
    assert all(x["lane"].lower() == "mid" for x in r["rows"])


def test_resolve_alias_synergy(store, ch_idx):
    r = empirical_synergy("ksante", min_games=1, top_k=2, store=store, champion_index=ch_idx)
    assert r["champion"] == "K'Sante"


def test_empty_paths(tmp_path: Path):
    ed = tmp_path / "data" / "empirical"
    ed.mkdir(parents=True)
    for name in ("synergies.jsonl", "counters.jsonl", "winrate.jsonl"):
        (ed / name).write_text("", encoding="utf-8")
    st = EmpiricalStore(root=tmp_path)
    r = empirical_synergy("X", store=st)
    assert r["pairs"] == []
