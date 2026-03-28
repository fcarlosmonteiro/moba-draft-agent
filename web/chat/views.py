from functools import wraps
from urllib.parse import quote, urlparse

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from chat.auth_env import SESSION_AUTH_KEY, credentials_match, resolve_web_password
from chat.graph_runner import run_chat_turn


def _safe_next(request) -> str:
    n = (request.GET.get("next") or request.POST.get("next") or "").strip()
    if n.startswith("/") and not n.startswith("//"):
        p = urlparse(n)
        if not p.netloc:
            return n
    return "/"


def web_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get(SESSION_AUTH_KEY):
            url = f"{reverse('login')}?next={quote(request.path, safe='')}"
            return redirect(url)
        return view_func(request, *args, **kwargs)

    return wrapper


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.session.get(SESSION_AUTH_KEY):
        return redirect(_safe_next(request))

    error: str | None = None
    if not resolve_web_password():
        error = "Defina DRAFT_WEB_PASSWORD (ou DRAFT_WEB_PASSWORD_B64) no ambiente."

    if request.method == "POST" and error is None:
        u = (request.POST.get("username") or "").strip()
        p = request.POST.get("password") or ""
        if credentials_match(u, p):
            request.session[SESSION_AUTH_KEY] = True
            request.session.modified = True
            return redirect(_safe_next(request))
        error = "Usuário ou senha incorretos."

    return render(
        request,
        "registration/login.html",
        {"error": error},
    )


@require_http_methods(["GET", "POST"])
def logout_view(request):
    request.session.flush()
    return redirect("login")


@web_login_required
@require_http_methods(["GET", "POST"])
def chat(request):
    history: list[list[str]] = request.session.get("chat_pairs", [])
    error: str | None = None

    if request.method == "POST":
        action = request.POST.get("action", "send")
        if action == "clear":
            request.session["chat_pairs"] = []
            request.session.modified = True
            return redirect("chat")

        text = (request.POST.get("message") or "").strip()
        if text:
            try:
                pairs = [(u, a) for u, a in history]
                reply = run_chat_turn(text, pairs)
                history = history + [[text, reply]]
                request.session["chat_pairs"] = history
                request.session.modified = True
            except Exception as exc:
                error = str(exc)

    return render(
        request,
        "chat/chat.html",
        {"history": history, "error": error},
    )
