# Plano de desenvolvimento (por fases)

Princípio: **entregar e validar uma fatia antes da próxima**. Cada fase tem critério de saída objetivo; não avançar sem ele.

**Referência técnica:** [`docs/agent.md`](agent.md).

---

## Meta do produto

Conversar com o usuário sobre pick/ban usando **estado de draft + dados locais**, com respostas **ancoradas** em tools (não estatística inventada), orquestradas por **LangGraph** e modelo via **OpenRouter**.

---

## Fase 0 — Fundações do projeto

| | |
|--|--|
| **Objetivo** | Repositório executável: Python versionado, dependências, raiz do projeto resolvida em runtime. |
| **Entregas** | `pyproject.toml`, `src/moba_draft_agent/` (`paths.project_root`), `.env.example`, testes em `tests/test_phase0.py`. |
| **Validação** | `pip install -e ".[dev]"`; `python -c "import moba_draft_agent"`; `pytest -q` passa. Instruções no README. |
| **Status** | Implementada. |

---

## Fase 1 — Carregar configuração (Camada 1)

| | |
|--|--|
| **Objetivo** | Ler `rules/draft-rules.yaml`, `catalog/champions.yaml`, `policies/assistant.md` a partir da raiz do repo. |
| **Entregas** | `moba_draft_agent.loaders`: `load_draft_rules`, `load_catalog`, `load_policies`, `ProjectConfig` (cache). Dependência `pyyaml`. |
| **Validação** | `pytest` em `tests/test_loaders.py`: parse sem exceção; `ranked_solo_draft` e `tournament_standard_draft` com 20 `steps`. |
| **Status** | Implementada. |

---

## Fase 2 — `resolve_champion`

| | |
|--|--|
| **Objetivo** | Normalizar string → campeão canônico (`id`/`name`) usando aliases do catálogo. |
| **Entregas** | `moba_draft_agent.champions`: `normalize_champion_query`, `ChampionIndex`, `ResolveResult`, `resolve_champion`. Variante sem apóstrofo para buscas (ex.: `ksante`). |
| **Validação** | `tests/test_resolve_champion.py`: nomes do CSV; amostra de 40 nomes únicos de `matches.csv`; casos `K'Sante`, `Jarvan IV`, vazio, desconhecido. |
| **Status** | Implementada. |

---

## Fase 3 — `validate_draft_state`

| | |
|--|--|
| **Objetivo** | Conferir `format_id`, `current_step_index`, bans/picks vs `steps` e regras de duplicidade. |
| **Entregas** | `moba_draft_agent.draft_state`: `DraftValidationResult`, `validate_draft_state` (contagens, replay, catálogo opcional). |
| **Validação** | `tests/test_draft_state.py`: vazio; contagens; índice inválido; desconhecido; duplicata global e no time; draft completo 20 passos. |
| **Status** | Implementada. |

---

## Fase 4 — Tools empíricas (Camada 2)

| | |
|--|--|
| **Objetivo** | Implementar leitura eficiente (stream/índice em memória na subida) de `synergies.jsonl`, `counters.jsonl`, `winrate.jsonl` com `min_games` e `top_k`. |
| **Entregas** | `moba_draft_agent.empirical`: `EmpiricalStore`, `empirical_synergy`, `empirical_counter`, `empirical_pair`, `empirical_lane_winrate`. |
| **Validação** | `tests/test_empirical.py` com dados reais (Aatrox/Ahri) e pasta vazia; alias via `ChampionIndex`. |
| **Status** | Implementada. |

---

## Fase 5 — Tools de partidas (Camada 3)

| | |
|--|--|
| **Objetivo** | Consultas parametrizadas sobre `data/matches/matches.csv` (sem SQL gerado pelo LLM). |
| **Entregas** | `moba_draft_agent.matches`: `MatchStore`, `matches_composition_stats`, `matches_champion_role_stats`, `matches_sample`, `matches_row_by_gameid`. |
| **Validação** | `tests/test_matches.py` com `LOLTMNT05_171038`, composição Gnar/…/Leona, Ahri mid azul, CSV vazio. |
| **Status** | Implementada. |

---

## Fase 6 — Modelo (OpenRouter) sem grafo

| | |
|--|--|
| **Objetivo** | Uma chamada de chat com system prompt = políticas + resumo das regras; sem tools. |
| **Entregas** | `moba_draft_agent.chat_openrouter`: `build_system_prompt`, `summarize_draft_rules`, `openrouter_chat_completion`, `draft_assistant_reply`. Dependência `openai`. |
| **Validação** | `tests/test_openrouter_smoke.py`: prompt local sempre; smoke com API só se `OPENROUTER_API_KEY` estiver definida. |
| **Status** | Implementada. |

---

## Fase 7 — LangGraph + tools

| | |
|--|--|
| **Objetivo** | `StateGraph` com estado (mensagens + `draft_state`), nó LLM com tools bindadas, loop até resposta final. |
| **Entregas** | Função `invoke` (e opcional `astream`) documentada. |
| **Validação** | Cenário E2E: pergunta que **obriga** pelo menos uma tool (ex.: sinergia de X) e a resposta menciona `games` ou dados retornados pela tool. |

---

## Fase 8 — Expor serviço (opcional)

| | |
|--|--|
| **Objetivo** | API HTTP (ex.: FastAPI) com body `{ "message", "draft_state" }` e resposta texto ou SSE. |
| **Entregas** | OpenAPI mínima, healthcheck. |
| **Validação** | `curl` ou teste de integração contra servidor local. |

---

## Ordem e paralelismo

- **Sequencial obrigatório:** 0 → 1 → 2 → 3 antes de confiar no estado do draft nas tools seguintes.
- **4 e 5** podem ser paralelizados entre dois devs depois da Fase 1 (só precisam de paths e catálogo para nomes).
- **6** pode começar cedo em paralelo às fases 4–5 (só API key).
- **7** depende de **4, 5 e 6**.

---

## Ritmo sugerido

1. Abrir **uma issue ou card por fase** com o critério de validação copiado deste doc.  
2. **PR pequeno** por fase (ou sub-tarefas dentro da fase).  
3. Marcar a fase como concluída só após o critério de validação (teste automatizado preferível a partir da Fase 1).

Atualize este arquivo se a ordem mudar (ex.: MVP sem Fase 8 ou sem partidas na primeira release).
