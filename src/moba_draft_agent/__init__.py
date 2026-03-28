"""Moba draft agent — pacote principal."""

from moba_draft_agent.champions import (
    ChampionIndex,
    ResolveResult,
    normalize_champion_query,
    resolve_champion,
)
from moba_draft_agent.draft_state import DraftValidationResult, validate_draft_state
from moba_draft_agent.empirical import (
    EmpiricalStore,
    empirical_counter,
    empirical_lane_winrate,
    empirical_pair,
    empirical_synergy,
)
from moba_draft_agent.loaders import (
    ProjectConfig,
    load_catalog,
    load_draft_rules,
    load_policies,
)
from moba_draft_agent.paths import project_root

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "project_root",
    "load_draft_rules",
    "load_catalog",
    "load_policies",
    "ProjectConfig",
    "normalize_champion_query",
    "ChampionIndex",
    "ResolveResult",
    "resolve_champion",
    "DraftValidationResult",
    "validate_draft_state",
    "EmpiricalStore",
    "empirical_synergy",
    "empirical_counter",
    "empirical_pair",
    "empirical_lane_winrate",
]
