"""Validação do estado do draft contra rules/draft-rules.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from moba_draft_agent.champions import ChampionIndex, normalize_champion_query
from moba_draft_agent.loaders import ProjectConfig, load_draft_rules


def _pick_champion_name(entry: Any) -> str:
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict):
        c = entry.get("champion")
        return str(c).strip() if c is not None else ""
    return ""


@dataclass
class DraftValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _format_steps(draft_rules: dict[str, Any], format_id: str) -> list[dict[str, Any]]:
    formats = draft_rules.get("formats") or {}
    fmt = formats.get(format_id)
    if not isinstance(fmt, dict):
        return []
    steps = fmt.get("steps")
    if not isinstance(steps, list):
        return []
    return steps


def validate_draft_state(
    state: dict[str, Any],
    *,
    draft_rules: dict[str, Any] | None = None,
    champion_index: ChampionIndex | None = None,
    config: ProjectConfig | None = None,
    require_known_champions: bool = True,
) -> DraftValidationResult:
    """
    Valida `format_id`, `current_step_index`, listas `bans`, `picks_blue`, `picks_red`.

    Convenção: `current_step_index` = quantidade de ações **já concluídas** (0 a N,
    com N = número de steps do formato). Próxima ação seria `steps[current_step_index]`.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if draft_rules is None:
        draft_rules = config.draft_rules if config is not None else load_draft_rules()

    format_id = state.get("format_id")
    if not format_id or not isinstance(format_id, str):
        errors.append("format_id ausente ou inválido.")
        return DraftValidationResult(False, errors, warnings)

    steps = _format_steps(draft_rules, format_id)
    if not steps:
        errors.append(f"Formato desconhecido ou sem steps: {format_id!r}.")
        return DraftValidationResult(False, errors, warnings)

    n = len(steps)
    idx = state.get("current_step_index", 0)
    if not isinstance(idx, int) or idx < 0 or idx > n:
        errors.append(
            f"current_step_index deve ser inteiro entre 0 e {n} (inclusivo); veio {idx!r}."
        )
        return DraftValidationResult(False, errors, warnings)

    bans = [str(b).strip() for b in (state.get("bans") or []) if str(b).strip()]
    picks_blue = [_pick_champion_name(p) for p in (state.get("picks_blue") or [])]
    picks_red = [_pick_champion_name(p) for p in (state.get("picks_red") or [])]
    picks_blue = [p for p in picks_blue if p]
    picks_red = [p for p in picks_red if p]

    ban_count = sum(1 for s in steps[:idx] if s.get("action") == "ban")
    blue_pick_count = sum(
        1 for s in steps[:idx] if s.get("action") == "pick" and s.get("side") == "blue"
    )
    red_pick_count = sum(
        1 for s in steps[:idx] if s.get("action") == "pick" and s.get("side") == "red"
    )

    if len(bans) != ban_count:
        errors.append(
            f"Esperados {ban_count} bans após {idx} ações; há {len(bans)} em bans."
        )
    if len(picks_blue) != blue_pick_count:
        errors.append(
            f"Esperados {blue_pick_count} picks azuis; há {len(picks_blue)} em picks_blue."
        )
    if len(picks_red) != red_pick_count:
        errors.append(
            f"Esperados {red_pick_count} picks vermelhos; há {len(picks_red)} em picks_red."
        )

    if errors:
        return DraftValidationResult(False, errors, warnings)

    ib = ir = bi = 0
    for i in range(idx):
        step = steps[i]
        action = step.get("action")
        side = step.get("side")
        if action == "ban":
            if bi >= len(bans):
                errors.append(f"Step {i}: faltou ban na lista bans.")
                break
            _ = bans[bi]
            bi += 1
        elif action == "pick":
            if side == "blue":
                if ib >= len(picks_blue):
                    errors.append(f"Step {i}: faltou pick azul em picks_blue.")
                    break
                ib += 1
            elif side == "red":
                if ir >= len(picks_red):
                    errors.append(f"Step {i}: faltou pick vermelho em picks_red.")
                    break
                ir += 1
            else:
                errors.append(f"Step {i}: side inválido {side!r}.")
                break
        else:
            errors.append(f"Step {i}: action inválida {action!r}.")
            break

    if errors:
        return DraftValidationResult(False, errors, warnings)

    if champion_index is None and config is not None:
        champion_index = ChampionIndex.from_catalog(config.catalog)

    def _cid(nm: str) -> str | None:
        if champion_index is None:
            return None
        rr = champion_index.resolve(nm)
        if rr.ok and rr.champion:
            return str(rr.champion["id"])
        return None

    if require_known_champions and champion_index is not None:
        for label, name in (
            *(("ban", b) for b in bans),
            *(("picks_blue", p) for p in picks_blue),
            *(("picks_red", p) for p in picks_red),
        ):
            r = champion_index.resolve(name)
            if not r.ok:
                if r.ambiguous:
                    errors.append(f"{label}: nome ambíguo {name!r}.")
                else:
                    errors.append(f"{label}: campeão desconhecido {name!r}.")

    if errors:
        return DraftValidationResult(False, errors, warnings)

    # Duplicidade (YAML: forbidden across rosters and within team)
    if champion_index is not None:
        all_ids: list[str] = []
        for b in bans:
            cid = _cid(b)
            if cid:
                all_ids.append(cid)
        blue_ids: list[str] = []
        for p in picks_blue:
            cid = _cid(p)
            if cid:
                all_ids.append(cid)
                blue_ids.append(cid)
        red_ids: list[str] = []
        for p in picks_red:
            cid = _cid(p)
            if cid:
                all_ids.append(cid)
                red_ids.append(cid)

        if len(all_ids) != len(set(all_ids)):
            errors.append("Campeão repetido (mesmo id em bans ou picks).")
        if len(blue_ids) != len(set(blue_ids)):
            errors.append("Pick repetido no time azul.")
        if len(red_ids) != len(set(red_ids)):
            errors.append("Pick repetido no time vermelho.")
    else:
        merged = [normalize_champion_query(x) for x in (*bans, *picks_blue, *picks_red)]
        if len(merged) != len(set(merged)):
            errors.append("Nome de campeão repetido (comparação normalizada, sem catálogo).")

    return DraftValidationResult(len(errors) == 0, errors, warnings)
