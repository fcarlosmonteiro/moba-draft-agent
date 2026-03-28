"""Uma instância do grafo por processo (worker Gunicorn)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

_graph: Any | None = None


def get_react_graph() -> Any:
    global _graph
    if _graph is None:
        from moba_draft_agent.agent_graph import create_draft_react_agent

        _graph = create_draft_react_agent()
    return _graph


def run_chat_turn(user_text: str, prior_pairs: list[tuple[str, str]]) -> str:
    """
    `prior_pairs`: (texto_usuário, texto_assistente) por turno anterior.
    Reconstrói Human/AI alternados e acrescenta o novo user.
    """
    graph = get_react_graph()
    messages = []
    for u, a in prior_pairs:
        messages.append(HumanMessage(content=u))
        messages.append(AIMessage(content=a))
    messages.append(HumanMessage(content=user_text))
    out = graph.invoke({"messages": messages})
    last = out["messages"][-1]
    if isinstance(last, AIMessage):
        return (last.content or "").strip()
    return str(last).strip()
