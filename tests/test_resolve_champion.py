import csv
from pathlib import Path

import pytest

from moba_draft_agent import ChampionIndex, load_catalog, project_root, resolve_champion
from moba_draft_agent.champions import normalize_champion_query


@pytest.fixture
def index():
    return ChampionIndex.from_catalog(load_catalog())


def test_normalize_apostrophe():
    assert normalize_champion_query("K\u2019Sante") == normalize_champion_query("K'Sante")


def test_resolve_exact_name_csv_like(index):
    for raw in (
        "K'Sante",
        "Cho'Gath",
        "Jarvan IV",
        "Miss Fortune",
        "Dr. Mundo",
        "Renata Glasc",
        "Zaahen",
        "Yunara",
        "Kai'Sa",
        "Bel'Veth",
    ):
        r = index.resolve(raw)
        assert r.ok, f"{raw!r}: {r.reason} {r.candidates}"
        assert r.champion is not None
        assert r.champion["name"] == raw or r.champion["id"] == raw


def test_resolve_alias_lowercase(index):
    r = index.resolve("ksante")
    assert r.ok
    assert r.champion["id"] == "K'Sante"


def test_resolve_jarvan_iv_alias(index):
    r = index.resolve("jarvan iv")
    assert r.ok
    assert r.champion["id"] == "Jarvan IV"


def test_resolve_empty(index):
    r = index.resolve("   ")
    assert not r.ok
    assert r.reason == "empty_query"


def test_resolve_unknown(index):
    r = index.resolve("xyznotachampion123")
    assert not r.ok
    assert r.reason == "not_found"


def test_resolve_champion_function_uses_disk():
    r = resolve_champion("Aatrox")
    assert r.ok
    assert r.champion["id"] == "Aatrox"


def test_matches_csv_sample_resolves(index):
    path = project_root() / "data" / "matches" / "matches.csv"
    if not path.is_file():
        pytest.skip("matches.csv ausente")

    names: set[str] = set()
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        champ_cols = [
            c
            for c in reader.fieldnames or []
            if c != "gameid" and c != "result"
        ]
        for row in reader:
            for c in champ_cols:
                v = (row.get(c) or "").strip()
                if v:
                    names.add(v)

    sample = sorted(names)[:40]
    assert len(sample) >= 20

    failures = []
    for name in sample:
        r = index.resolve(name)
        if not r.ok:
            failures.append((name, r.reason, r.ambiguous))

    assert not failures, f"Falhas: {failures[:10]}"
