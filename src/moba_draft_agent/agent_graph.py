"""LangGraph ReAct + tools (OpenRouter)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Annotated, Any, Literal, NotRequired, Sequence, cast

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import create_react_agent
from typing_extensions import TypedDict

from moba_draft_agent.chat_openrouter import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    build_system_prompt,
)
from moba_draft_agent.champions import ChampionIndex, resolve_champion
from moba_draft_agent.draft_state import validate_draft_state
from moba_draft_agent.empirical import (
    EmpiricalStore,
    empirical_counter,
    empirical_lane_winrate,
    empirical_pair,
    empirical_synergy,
)
from moba_draft_agent.loaders import ProjectConfig
from moba_draft_agent.matches import (
    MatchStore,
    Side,
    matches_champion_role_stats,
    matches_composition_stats,
    matches_row_by_gameid,
    matches_sample,
)


def build_react_system_prompt(config: ProjectConfig | None = None) -> str:
    extra = (
        "\n\n---\n\n"
        "Você dispõe de tools: use-as para fatos (catálogo, validação de draft, "
        "dados empíricos JSONL, partidas CSV). Não cite winrate, `games` ou contagens "
        "sem ter obtido via tool nesta conversa."
    )
    return build_system_prompt(config) + extra


class DraftAssistantState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    remaining_steps: NotRequired[RemainingSteps]
    draft_state: NotRequired[dict[str, Any] | None]


def _json_line(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def create_draft_react_agent(
    config: ProjectConfig | None = None,
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.4,
):
    """Requer `OPENROUTER_API_KEY` ou `api_key=`."""
    cfg = config or ProjectConfig()
    index = ChampionIndex.from_catalog(cfg.catalog)
    emp = EmpiricalStore(root=cfg.root)
    mst = MatchStore(root=cfg.root)

    @tool
    def tool_resolve_champion(query: str) -> str:
        """Resolve texto do usuário para entrada do catálogo (id, name, aliases)."""
        r = resolve_champion(query, index=index)
        return _json_line(asdict(r))

    @tool
    def tool_validate_draft_state_json(draft_json: str) -> str:
        """JSON: format_id, current_step_index, bans, picks_blue, picks_red."""
        try:
            state = json.loads(draft_json)
        except json.JSONDecodeError as e:
            return _json_line({"ok": False, "errors": [f"JSON inválido: {e}"]})
        if not isinstance(state, dict):
            return _json_line({"ok": False, "errors": ["A raiz deve ser um objeto JSON."]})
        vr = validate_draft_state(state, champion_index=index, config=cfg)
        return _json_line(asdict(vr))

    @tool
    def tool_empirical_synergy(champion: str, min_games: int = 10, top_k: int = 8) -> str:
        """Sinergias empíricas em que o campeão aparece; filtra por min_games; top_k pares."""
        return _json_line(
            empirical_synergy(
                champion,
                min_games=min_games,
                top_k=top_k,
                store=emp,
                champion_index=index,
            )
        )

    @tool
    def tool_empirical_counter(champion: str, min_games: int = 10, top_k: int = 8) -> str:
        """Counters empíricos (foco em champion1); min_games e top_k."""
        return _json_line(
            empirical_counter(
                champion,
                min_games=min_games,
                top_k=top_k,
                store=emp,
                champion_index=index,
            )
        )

    @tool
    def tool_empirical_pair(champion_a: str, champion_b: str, relation: str) -> str:
        """Uma linha exata entre dois campeões. relation: synergy ou counter."""
        rel = relation.strip().lower()
        if rel not in ("synergy", "counter"):
            return _json_line({"error": "relation deve ser synergy ou counter"})
        rel_t = cast(Literal["synergy", "counter"], rel)
        return _json_line(
            empirical_pair(
                champion_a,
                champion_b,
                relation=rel_t,
                store=emp,
                champion_index=index,
            )
        )

    @tool
    def tool_empirical_lane_winrate(
        champion: str, min_games: int = 10, lane: str = ""
    ) -> str:
        """Winrate por rota (empírico); deixe lane vazio para todas acima de min_games."""
        lane_opt: str | None = lane.strip() or None
        return _json_line(
            empirical_lane_winrate(
                champion,
                min_games=min_games,
                lane=lane_opt,
                store=emp,
                champion_index=index,
            )
        )

    @tool
    def tool_matches_composition(side: str, roster_json: str) -> str:
        """side blue|red; roster_json com top, jungle, mid, bottom, support."""
        s = side.strip().lower()
        if s not in ("blue", "red"):
            return _json_line({"error": "side deve ser blue ou red"})
        try:
            roster = json.loads(roster_json)
        except json.JSONDecodeError as e:
            return _json_line({"error": f"roster JSON inválido: {e}"})
        if not isinstance(roster, dict):
            return _json_line({"error": "roster deve ser um objeto JSON"})
        try:
            return _json_line(
                matches_composition_stats(
                    cast(Side, s),
                    roster,
                    store=mst,
                    champion_index=index,
                )
            )
        except ValueError as e:
            return _json_line({"error": str(e)})

    @tool
    def tool_matches_champion_role(champion: str, side: str, role: str) -> str:
        """Partidas no CSV: campeão em um papel (top,jungle,mid,bottom,support) e lado blue|red."""
        s = side.strip().lower()
        if s not in ("blue", "red"):
            return _json_line({"error": "side deve ser blue ou red"})
        try:
            return _json_line(
                matches_champion_role_stats(
                    champion,
                    cast(Side, s),
                    role,
                    store=mst,
                    champion_index=index,
                )
            )
        except ValueError as e:
            return _json_line({"error": str(e)})

    @tool
    def tool_matches_sample_rows(limit: int = 10, offset: int = 0) -> str:
        """Amostra ordenada de linhas do matches.csv (limit, offset)."""
        return _json_line(matches_sample(limit=limit, offset=offset, store=mst))

    @tool
    def tool_matches_by_gameid(gameid: str) -> str:
        """Busca uma partida pelo gameid no CSV."""
        return _json_line(matches_row_by_gameid(gameid, store=mst))

    tools = [
        tool_resolve_champion,
        tool_validate_draft_state_json,
        tool_empirical_synergy,
        tool_empirical_counter,
        tool_empirical_pair,
        tool_empirical_lane_winrate,
        tool_matches_composition,
        tool_matches_champion_role,
        tool_matches_sample_rows,
        tool_matches_by_gameid,
    ]

    key = (api_key or os.environ.get("OPENROUTER_API_KEY", "") or "").strip()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY não definida. Exporte a chave ou passe api_key=."
        )
    m = (model or os.environ.get("OPENROUTER_MODEL") or "").strip() or DEFAULT_MODEL
    url = (base_url or os.environ.get("OPENROUTER_BASE_URL") or "").strip() or DEFAULT_BASE_URL

    llm = ChatOpenAI(
        model=m,
        base_url=url,
        api_key=key,
        temperature=temperature,
    )
    prompt = build_react_system_prompt(cfg)
    return create_react_agent(
        llm,
        tools,
        prompt=prompt,
        state_schema=DraftAssistantState,
        version="v2",
    )


def invoke_draft_react(
    user_text: str,
    *,
    graph: Any | None = None,
    config: ProjectConfig | None = None,
    draft_state: dict[str, Any] | None = None,
    **agent_kwargs: Any,
) -> dict[str, Any]:
    """Passe `graph` para não recriar tools a cada mensagem."""
    g = graph or create_draft_react_agent(config=config, **agent_kwargs)
    payload: dict[str, Any] = {"messages": [HumanMessage(content=user_text)]}
    if draft_state is not None:
        payload["draft_state"] = draft_state
    return g.invoke(payload)
