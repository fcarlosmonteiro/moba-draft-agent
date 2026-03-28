# Interface web (Django)

Chat experimental com login; pensado para deploy no **Render**.

## Instalação local

Na **raiz do repositório**:

```bash
pip install -e ".[web,dev]"
cd web
python manage.py migrate
```

Crie o usuário de login (senha **não** vai para o Git — use o seu `.env`):

```bash
# No .env na raiz do repo, por exemplo:
# DRAFT_WEB_USER=admin
# DRAFT_WEB_PASSWORD="moba#draft123"

python manage.py ensure_login_user
python manage.py runserver
```

Abra http://127.0.0.1:8000/ — faça login e use o chat. É necessário `OPENROUTER_API_KEY` no `.env` (raiz do repo).

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `OPENROUTER_API_KEY` | Obrigatório para o agente responder |
| `DRAFT_WEB_USER` | Login (padrão `admin`) |
| `DRAFT_WEB_PASSWORD` | Senha — **obrigatória** para `ensure_login_user` |
| `DJANGO_SECRET_KEY` | Obrigatório em produção (string longa aleatória) |
| `DJANGO_DEBUG` | `1` local, `0` no Render |
| `DJANGO_ALLOWED_HOSTS` | Lista separada por vírgula (ex.: `meu-app.onrender.com,.onrender.com`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://meu-app.onrender.com` em HTTPS |
| `DATABASE_URL` | Opcional; se definido, usa Postgres (Render) em vez de SQLite |
| `MOBA_DRAFT_ROOT` | Opcional; por padrão é a raiz do repositório (pai de `web/`) |

## Render

1. **Root directory:** raiz do repo (onde está `pyproject.toml`).
2. **Build command:** `pip install -e ".[web]" && cd web && python manage.py collectstatic --noinput`
3. **Start command:** `cd web && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. **Pre-deploy** (ou comando único antes do start):  
   `cd web && python manage.py migrate --noinput && python manage.py ensure_login_user`
5. No painel, defina **Environment**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `OPENROUTER_API_KEY`, `DRAFT_WEB_PASSWORD` (e opcionalmente `DRAFT_WEB_USER`), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.

SQLite no disco efêmero do Render pode perder o banco a cada deploy; para persistir sessão/usuários, crie um **PostgreSQL** grátis no Render e ligue `DATABASE_URL` (já suportado em `settings.py`).

Veja também [`render.yaml`](../render.yaml) no repositório.
