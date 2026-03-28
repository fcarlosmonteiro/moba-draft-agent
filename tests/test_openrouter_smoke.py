"""Fase 6 — smoke OpenRouter (opcional, requer OPENROUTER_API_KEY)."""

import os

import pytest

from moba_draft_agent import ProjectConfig, build_system_prompt, draft_assistant_reply


def test_build_system_prompt_contains_policies_and_rules():
    cfg = ProjectConfig()
    text = build_system_prompt(cfg)
    assert "assistente" in text.lower() or "draft" in text.lower()
    assert "20" in text or "bans" in text.lower()


def test_openrouter_missing_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from moba_draft_agent.chat_openrouter import openrouter_chat_completion

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        openrouter_chat_completion([{"role": "user", "content": "oi"}])


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY", "").strip(),
    reason="OPENROUTER_API_KEY não definida — smoke de rede omitido",
)
def test_draft_assistant_reply_smoke():
    out = draft_assistant_reply(
        "Em uma frase: o que é ban no draft do LoL?",
        model=os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"),
    )
    assert len(out) > 10
