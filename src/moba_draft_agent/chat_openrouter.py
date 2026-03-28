"""Fase 6 — uma chamada de chat via OpenRouter (sem LangGraph, sem tools)."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from moba_draft_agent.loaders import ProjectConfig

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"


def summarize_draft_rules(rules: dict[str, Any]) -> str:
    """Texto curto para o system prompt (não envia o YAML inteiro)."""
    fmt = (rules.get("formats") or {}).get("ranked_solo_draft") or {}
    steps = fmt.get("steps") or []
    totals = fmt.get("totals") or {}
    meta = rules.get("meta") or {}
    game = meta.get("game", "league_of_legends")
    return (
        f"Contexto mecânico (League of Legends / {game}): draft ranqueado de referência "
        f"com {len(steps)} ações na ordem oficial (bans e picks alternados entre azul e vermelho). "
        f"Por time: {totals.get('bans_per_team', 5)} bans e {totals.get('picks_per_team', 5)} picks. "
        "O usuário pode enviar o estado do draft em JSON; não invente winrate ou estatísticas "
        "se não tiver sido fornecido dado de ferramenta nesta conversa."
    )


def build_system_prompt(config: ProjectConfig | None = None) -> str:
    """Políticas (`assistant.md`) + resumo das regras de draft."""
    cfg = config or ProjectConfig()
    policies = cfg.policies.strip()
    summary = summarize_draft_rules(cfg.draft_rules)
    return f"{policies}\n\n---\n\n{summary}"


def openrouter_chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """
    Chat Completions compatível com OpenAI, apontando para OpenRouter.
    Variáveis: OPENROUTER_API_KEY, OPENROUTER_MODEL (opcional).
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY não definida. Exporte a chave ou passe api_key=."
        )
    m = (model or os.environ.get("OPENROUTER_MODEL") or "").strip() or DEFAULT_MODEL
    url = (base_url or os.environ.get("OPENROUTER_BASE_URL") or "").strip() or DEFAULT_BASE_URL

    client = OpenAI(base_url=url, api_key=key)
    resp = client.chat.completions.create(
        model=m,
        messages=messages,
        temperature=0.4,
    )
    choice = resp.choices[0].message
    return (choice.content or "").strip()


def draft_assistant_reply(
    user_message: str,
    *,
    config: ProjectConfig | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    """
    Uma troca: system (políticas + resumo das regras) + mensagem do usuário.
    Próxima fase (LangGraph): substituir por grafo com tools.
    """
    system = build_system_prompt(config)
    return openrouter_chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        model=model,
        api_key=api_key,
    )
