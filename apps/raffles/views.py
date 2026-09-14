"""Views do app raffles — Fase 2."""

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.instagram.client import InstagramAPIError, InstagramClient
from apps.raffles.models import Draw, Raffle, Winner

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_raffle_for_user(uuid, user):
    """Retorna o sorteio do usuário ou 403."""
    raffle = get_object_or_404(Raffle, uuid=uuid)
    if raffle.user != user:
        return None, HttpResponseForbidden()
    return raffle, None


def _instagram_client(user):
    try:
        return InstagramClient(user.instagram_account.access_token)
    except Exception:
        return None


# ── Painel ────────────────────────────────────────────────────────────────────

@login_required
def painel(request):
    """Dashboard: saldo + últimos sorteios + CTA novo sorteio."""
    raffles = Raffle.objects.filter(user=request.user).order_by("-created_at")[:10]
    return render(request, "raffles/painel.html", {
        "raffles": raffles,
        "balance": request.user.credit_balance(),
    })


# ── Histórico ─────────────────────────────────────────────────────────────────

@login_required
def historico(request):
    """Lista todos os sorteios do usuário."""
    qs = Raffle.objects.filter(user=request.user).order_by("-created_at")

    status_filter = request.GET.get("status", "")
    if status_filter:
        qs = qs.filter(status=status_filter)

    return render(request, "raffles/historico.html", {
        "raffles": qs,
        "status_filter": status_filter,
        "STATUS_CHOICES": Raffle.STATUS_CHOICES,
    })


# ── Novo sorteio — seleção de post ────────────────────────────────────────────

@login_required
def novo(request):
    """
    GET  — grade de posts + campo de busca por link.
    POST — cria Raffle, dispara task de carregamento, redireciona para /carregar/.
    """
    if request.method == "POST":
        ig_media_id = request.POST.get("ig_media_id", "").strip()
        permalink    = request.POST.get("permalink", "").strip()
        caption      = request.POST.get("caption", "").strip()
        thumbnail_url = request.POST.get("thumbnail_url", "").strip()
        media_type   = request.POST.get("media_type", "").strip()

        if not ig_media_id:
            posts_list, _, _ = _load_posts(request.user)
            return render(request, "raffles/novo.html", {
                "error": "Selecione um post.",
                "posts": posts_list,
            })

        raffle = Raffle.objects.create(
            user=request.user,
            ig_media_id=ig_media_id,
            permalink=permalink,
            caption=caption,
            thumbnail_url=thumbnail_url,
            media_type=media_type,
            status=Raffle.STATUS_DRAFT,
        )

        from apps.raffles.tasks import load_comments
        load_comments.delay(raffle.pk)

        return redirect("raffles:carregar", uuid=raffle.uuid)

    # GET
    after = request.GET.get("after", "")
    posts, next_cursor, error = _load_posts(request.user, after=after or None)
    return render(request, "raffles/novo.html", {
        "posts": posts,
        "error": error,
        "after": next_cursor,
    })


def _load_posts(user, after=None):
    """Retorna (posts_list, next_cursor, error_msg)."""
    client = _instagram_client(user)
    if not client:
        return [], "", "Conta do Instagram não conectada."
    try:
        data = client.get_media(after=after)
        posts = data.get("data", [])
        for post in posts:
            post["thumbnail"] = post.get("thumbnail_url") or post.get("media_url", "")
        next_cursor = data.get("paging", {}).get("cursors", {}).get("after", "")
        return posts, next_cursor, ""
    except InstagramAPIError as e:
        logger.warning("Erro ao carregar posts para @%s: %s", user.username, e)
        return [], "", f"Erro ao carregar posts: {e}"


# HTMX: carregar mais posts
@login_required
def posts_fragment(request):
    """Fragmento HTMX para 'carregar mais posts'."""
    after = request.GET.get("after", "")
    posts, next_cursor, error = _load_posts(request.user, after=after or None)
    return render(request, "raffles/_posts.html", {
        "posts": posts,
        "error": error,
        "after": next_cursor,
    })


# ── Carregando comentários ────────────────────────────────────────────────────

@login_required
def carregar(request, uuid):
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err

    # Se já ficou pronto, redireciona para regras
    if raffle.status == Raffle.STATUS_READY:
        return redirect("raffles:regras", uuid=uuid)
    if raffle.status == Raffle.STATUS_DRAWN:
        return redirect("raffles:resultado", uuid=uuid)

    return render(request, "raffles/carregar.html", {"raffle": raffle})


@login_required
def progresso_fragment(request, uuid):
    """HTMX polling: retorna fragmento com progresso atual."""
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err
    return render(request, "raffles/_progresso.html", {"raffle": raffle})


# ── Regras ────────────────────────────────────────────────────────────────────

@login_required
def regras(request, uuid):
    """
    GET  — exibe form de regras + contagem de participantes.
    POST — salva regras e redireciona para /sortear/.
    """
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err

    if raffle.status not in (Raffle.STATUS_READY, Raffle.STATUS_DRAWN):
        return redirect("raffles:carregar", uuid=uuid)

    if request.method == "POST":
        _apply_rules_from_post(raffle, request.POST)
        return redirect("raffles:sortear", uuid=uuid)

    return render(request, "raffles/regras.html", {
        "raffle": raffle,
        "participants_count": len(raffle.get_participants()),
    })


@login_required
def participantes_fragment(request, uuid):
    """HTMX: retorna contagem de participantes com as regras atuais do form."""
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err

    # Aplica regras temporariamente (sem salvar)
    _apply_rules_from_post(raffle, request.GET, save=False)
    count = len(raffle.get_participants())
    return render(request, "raffles/_participantes_count.html", {
        "count": count,
    })


def _apply_rules_from_post(raffle, data, save=True):
    raffle.unique_per_user   = data.get("unique_per_user") == "on"
    raffle.include_replies   = data.get("include_replies") == "on"
    raffle.exclude_owner     = data.get("exclude_owner", "on") == "on"
    raffle.min_mentions      = int(data.get("min_mentions") or 0)
    raffle.required_keyword  = data.get("required_keyword", "").strip()
    raffle.winners_count     = max(1, int(data.get("winners_count") or 1))
    raffle.alternates_count  = max(0, int(data.get("alternates_count") or 0))

    raw_excluded = data.get("excluded_usernames", "").strip()
    raffle.excluded_usernames = [
        u.lstrip("@").strip().lower()
        for u in raw_excluded.replace(",", "\n").splitlines()
        if u.strip()
    ]

    if save:
        raffle.save(update_fields=[
            "unique_per_user", "include_replies", "exclude_owner",
            "min_mentions", "required_keyword", "winners_count",
            "alternates_count", "excluded_usernames",
        ])


# ── Sortear ───────────────────────────────────────────────────────────────────

@login_required
def sortear(request, uuid):
    """
    GET  — tela de animação (o sorteio já foi feito; resultado em sessão).
    POST — executa sorteio e redireciona para GET (PRG pattern).
    """
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        balance = request.user.credit_balance()

        if raffle.status != Raffle.STATUS_DRAWN and balance < 1:
            return redirect("pages:planos")

        try:
            draw, winners, alternates = raffle.draw(reason=reason)
        except ValueError as e:
            return render(request, "raffles/sortear.html", {
                "raffle": raffle,
                "error": str(e),
            })

        return redirect("raffles:resultado", uuid=uuid)

    # GET — mostra animação; se já sorteado, vai direto para resultado
    if raffle.status == Raffle.STATUS_DRAWN:
        # Formulário de re-sorteio (vem de resultado.html)
        return redirect("raffles:resultado", uuid=uuid)

    if raffle.status != Raffle.STATUS_READY:
        return redirect("raffles:carregar", uuid=uuid)

    return render(request, "raffles/sortear.html", {
        "raffle": raffle,
        "balance": request.user.credit_balance(),
    })


# ── Resultado ─────────────────────────────────────────────────────────────────

@login_required
def resultado(request, uuid):
    raffle, err = _get_raffle_for_user(uuid, request.user)
    if err:
        return err

    if raffle.status != Raffle.STATUS_DRAWN:
        return redirect("raffles:regras", uuid=uuid)

    last_draw = raffle.draws.order_by("-round").first()
    all_draws = raffle.draws.prefetch_related("winners").order_by("round")

    return render(request, "raffles/resultado.html", {
        "raffle": raffle,
        "last_draw": last_draw,
        "all_draws": all_draws,
        "balance": request.user.credit_balance(),
    })


# ── Certificado público ───────────────────────────────────────────────────────

def certificado(request, uuid):
    """Página pública de certificado — não exige login."""
    raffle = get_object_or_404(Raffle, uuid=uuid, status=Raffle.STATUS_DRAWN)
    all_draws = raffle.draws.prefetch_related("winners").order_by("round")
    last_draw = all_draws.last()

    return render(request, "raffles/certificado.html", {
        "raffle": raffle,
        "all_draws": all_draws,
        "last_draw": last_draw,
    })
