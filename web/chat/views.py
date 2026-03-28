from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from chat.graph_runner import run_chat_turn


@login_required
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
