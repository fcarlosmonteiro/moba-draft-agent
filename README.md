# moba-draft-agent

Agente de conversação para apoio a pick/ban em League of Legends (regras, catálogo, sinergias/counters agregados, partidas profissionais).

- **Especificação e diagramas:** [`docs/agent.md`](docs/agent.md)
- **Plano por fases (metas e validação):** [`docs/development.md`](docs/development.md)

## Desenvolvimento

Requisito: **Python 3.11+**.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Fase 0 — checagem rápida**

```bash
python -c "import moba_draft_agent; print(moba_draft_agent.__version__, moba_draft_agent.project_root())"
pytest -q
```

Variáveis: copie [`.env.example`](.env.example) para `.env` (não versionado). Esquema dos dados em [`docs/agent.md`](docs/agent.md).

## Web (Django)

Chat Django (login por env, sem banco): [`web/README.md`](web/README.md). Deploy: [`render.yaml`](render.yaml).