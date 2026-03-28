import pytest

from moba_draft_agent import ChampionIndex, load_catalog, load_draft_rules, validate_draft_state


@pytest.fixture
def rules():
    return load_draft_rules()


@pytest.fixture
def ch_idx():
    return ChampionIndex.from_catalog(load_catalog())


def test_empty_draft_valid(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 0,
        "bans": [],
        "picks_blue": [],
        "picks_red": [],
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert r.ok
    assert r.errors == []


def test_six_bans_only(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 6,
        "bans": ["A", "B", "C", "D", "E", "F"],
        "picks_blue": [],
        "picks_red": [],
    }
    r = validate_draft_state(
        st, draft_rules=rules, champion_index=ch_idx, require_known_champions=False
    )
    assert r.ok


def test_wrong_ban_count(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 6,
        "bans": ["A", "B"],
        "picks_blue": [],
        "picks_red": [],
    }
    r = validate_draft_state(
        st, draft_rules=rules, champion_index=ch_idx, require_known_champions=False
    )
    assert not r.ok
    assert any("bans" in e for e in r.errors)


def test_index_out_of_range(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 21,
        "bans": [],
        "picks_blue": [],
        "picks_red": [],
    }
    r = validate_draft_state(
        st, draft_rules=rules, champion_index=ch_idx, require_known_champions=False
    )
    assert not r.ok
    assert any("current_step_index" in e for e in r.errors)


def test_unknown_champion(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 1,
        "bans": ["NotARealChampionXyz"],
        "picks_blue": [],
        "picks_red": [],
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert not r.ok
    assert any("desconhecido" in e for e in r.errors)


def test_duplicate_across_ban_and_pick(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 7,
        "bans": ["Aatrox", "Ahri", "Akali", "Akshan", "Alistar", "Ambessa"],
        "picks_blue": ["Aatrox"],
        "picks_red": [],
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert not r.ok
    assert any("repetido" in e for e in r.errors)


def test_duplicate_same_team_blue(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 10,
        "bans": ["Aatrox", "Ahri", "Akali", "Akshan", "Alistar", "Ambessa"],
        "picks_blue": ["Amumu", "Amumu"],
        "picks_red": ["Anivia", "Annie"],
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert not r.ok
    assert any("time azul" in e for e in r.errors)


def test_pick_as_dict_champion(rules, ch_idx):
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 7,
        "bans": ["Aatrox", "Ahri", "Akali", "Akshan", "Alistar", "Ambessa"],
        "picks_blue": [{"champion": "Amumu", "role": "jungle"}],
        "picks_red": [],
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert r.ok


def test_completed_draft_20_steps(rules, ch_idx):
    bans = [
        "Aatrox",
        "Ahri",
        "Akali",
        "Akshan",
        "Alistar",
        "Ambessa",
        "Amumu",
        "Anivia",
        "Annie",
        "Aphelios",
    ]
    pb = ["Ashe", "Aurelion Sol", "Aurora", "Azir", "Bard"]
    pr = ["Bel'Veth", "Blitzcrank", "Brand", "Braum", "Briar"]
    st = {
        "format_id": "ranked_solo_draft",
        "current_step_index": 20,
        "bans": bans,
        "picks_blue": pb,
        "picks_red": pr,
    }
    r = validate_draft_state(st, draft_rules=rules, champion_index=ch_idx)
    assert r.ok
