"""Fase 7 — grafo ReAct + tools (smoke opcional com OPENROUTER_API_KEY)."""

import os

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from moba_draft_agent import ProjectConfig, build_react_system_prompt
from moba_draft_agent.agent_graph import create_draft_react_agent


def test_build_react_system_prompt_mentions_tools():
    text = build_react_system_prompt(ProjectConfig())
    assert "tool" in text.lower() or "ferrament" in text.lower()


def test_create_draft_react_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        create_draft_react_agent()


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY", "").strip(),
    reason="OPENROUTER_API_KEY não definida — smoke LangGraph omitido",
)
def test_react_agent_synergy_smoke_uses_empirical_tool():
    graph = create_draft_react_agent(
        model=os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"),
        temperature=0,
    )
    question = (
        "Quais sinergias empíricas do campeão Aatrox com pelo menos 10 jogos? "
        "Use a ferramenta de sinergia empírica (não invente números). "
        "Na resposta final, mencione explicitamente o campo games de pelo menos um par."
    )
    msgs = []
    for _ in range(4):
        out = graph.invoke({"messages": [HumanMessage(content=question)]})
        msgs = out["messages"]
        tool_msgs = [m for m in msgs if isinstance(m, ToolMessage)]
        tool_text = " ".join((m.content or "").lower() for m in tool_msgs)
        if tool_msgs and "aatrox" in tool_text and "games" in tool_text:
            break
    else:
        pytest.fail("smoke: após várias tentativas, não houve tool com dados de Aatrox/games")

    tool_msgs = [m for m in msgs if isinstance(m, ToolMessage)]
    tool_text = " ".join((m.content or "").lower() for m in tool_msgs)
    final = msgs[-1]
    assert isinstance(final, AIMessage)
    body = (final.content or "").lower()
    assert "games" in body or "games" in tool_text
