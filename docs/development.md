# Plano por fases

Validar cada fatia antes da próxima. Detalhe técnico: [`agent.md`](agent.md).

**Meta:** conversa sobre pick/ban com dados locais e respostas ancoradas em tools (LangGraph + OpenRouter).

| Fase | Entrega principal | Status |
|------|-------------------|--------|
| 0 | `pyproject`, `project_root`, testes import | OK |
| 1 | `loaders`, `ProjectConfig` | OK |
| 2 | `resolve_champion` | OK |
| 3 | `validate_draft_state` | OK |
| 4 | `empirical_*` + JSONL | OK |
| 5 | `matches_*` + CSV | OK |
| 6 | `chat_openrouter` (sem tools) | OK |
| 7 | `agent_graph` LangGraph + tools | OK |
| 8 | HTTP — app Django em `web/` (Render: `render.yaml`) | MVP em andamento |

Dependências: 2–3 precisam de 1; 7 precisa de 4–6. **8** é opcional para MVP web.
