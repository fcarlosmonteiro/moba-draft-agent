import moba_draft_agent
from moba_draft_agent import (
    ProjectConfig,
    load_catalog,
    load_draft_rules,
    load_policies,
)


def test_load_draft_rules_real_file():
    rules = load_draft_rules()
    assert "formats" in rules
    ranked = rules["formats"]["ranked_solo_draft"]
    assert len(ranked["steps"]) == 20
    tournament = rules["formats"]["tournament_standard_draft"]
    assert len(tournament["steps"]) == 20


def test_load_catalog_has_champions():
    cat = load_catalog()
    assert "champions" in cat
    assert len(cat["champions"]) >= 1


def test_load_policies_non_empty():
    text = load_policies()
    assert "assistente" in text.lower() or "draft" in text.lower()


def test_project_config_caches():
    cfg = ProjectConfig(root=moba_draft_agent.project_root())
    r1 = cfg.draft_rules
    r2 = cfg.draft_rules
    assert r1 is r2
    cfg.clear_cache()
    r3 = cfg.draft_rules
    assert r3 == r1
    assert r3 is not r1
