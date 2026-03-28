# Interface web (Django) — MVP sem banco

Login **só com variáveis de ambiente** (`DRAFT_WEB_USER` / `DRAFT_WEB_PASSWORD`). Sessão em **cookie assinado** (sem SQLite/Postgres, sem `migrate`).

## Local

Na **raiz do repositório**:

```bash
pip install -e ".[web,dev]"
cd web
python manage.py runserver
```

No `.env` na raiz do repo, por exemplo:

```env
DRAFT_WEB_USER=admin
DRAFT_WEB_PASSWORD=mobadraft2026
OPENROUTER_API_KEY=...
```

Abra http://127.0.0.1:8000/login — não há `ensure_login_user` nem banco.

**Senha com `#`:** use aspas no `.env` ou `DRAFT_WEB_PASSWORD_B64` (`python -c "import base64; print(base64.b64encode(b'sua_senha').decode())"`).

**Histórico longo no chat:** o cookie de sessão tem limite de tamanho; para conversas enormes, use “Limpar histórico”.

## Variáveis

| Variável | Uso |
|----------|-----|
| `OPENROUTER_API_KEY` | Obrigatório para o agente |
| `DRAFT_WEB_USER` | Login (padrão `admin` se omitido) |
| `DRAFT_WEB_PASSWORD` | Senha (plain ou com aspas se tiver `#`) |
| `DRAFT_WEB_PASSWORD_B64` | Opcional; sobrepõe a senha em texto |
| `DJANGO_SECRET_KEY` | Obrigatório em produção (assinatura do cookie de sessão) |
| `DJANGO_DEBUG` | `1` local, `0` no Render |
| `DJANGO_ALLOWED_HOSTS` | Ex.: `meu-app.onrender.com,.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://meu-app.onrender.com` |

## Render

1. Root = raiz do repo (`pyproject.toml`).
2. **Build:** `pip install -e ".[web]" && cd web && python manage.py collectstatic --noinput`
3. **Start:** `cd web && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. **Sem** pre-deploy de migrate.
5. Environment: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `OPENROUTER_API_KEY`, `DRAFT_WEB_PASSWORD`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.

Blueprint: [`render.yaml`](../render.yaml).
