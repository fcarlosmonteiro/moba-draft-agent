# moba-draft-agent

Assistente de **draft** (pick/ban) para League of Legends: conversa em linguagem natural com respostas ancoradas em **dados locais** (regras, catálogo, agregados empíricos, partidas em CSV). O modelo fala via **OpenRouter**; a orquestração com tools usa **LangGraph** (ReAct).

## Documentação

| Doc | Conteúdo |
|-----|----------|
| [`docs/agent.md`](docs/agent.md) | Dados, fluxo, diagramas, contrato do draft em JSON |
| [`docs/development.md`](docs/development.md) | Fases do projeto e status |

## Requisitos

- **Python 3.11+**
- Chave **[OpenRouter](https://openrouter.ai/)** para chamadas ao LLM (`OPENROUTER_API_KEY`)

## Instalação

```bash
python3 -m venv .venv
source .venv/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"        # pacote + testes
# opcional — interface web:
pip install -e ".[web,dev]"
```

Copie [`.env.example`](.env.example) para **`.env`** na raiz do repositório e preencha (arquivo **não** é versionado).

## Uso rápido — biblioteca

```bash
python -c "import moba_draft_agent as m; print(m.__version__, m.project_root())"
pytest -q
```

O pacote resolve a raiz do repo pelo arquivo `rules/draft-rules.yaml` (ou `MOBA_DRAFT_ROOT`).

## Interface web (Django)

MVP com **login por variáveis de ambiente** (`DRAFT_WEB_USER` / `DRAFT_WEB_PASSWORD`), **sem banco** (sessão em cookie assinado).

```bash
pip install -e ".[web,dev]"
cd web
python manage.py runserver
```

Abra http://127.0.0.1:8000/login — o `.env` na raiz deve incluir `OPENROUTER_API_KEY` e as variáveis `DRAFT_WEB_*`.

Detalhes, tabela de variáveis e deploy: **[`web/README.md`](web/README.md)** · blueprint **[`render.yaml`](render.yaml)**.

## Estrutura (resumo)

```
catalog/          # champions.yaml
rules/            # draft-rules.yaml
policies/         # assistant.md (system prompt)
data/empirical/   # JSONL (sinergias, counters, winrate)
data/matches/     # matches.csv
src/moba_draft_agent/   # pacote Python (loaders, grafo, tools)
web/              # Django (chat)
tests/
```

## Licença

Ver [LICENSE](LICENSE).
