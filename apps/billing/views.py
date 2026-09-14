"""Views de billing — compra de créditos e minha conta."""

import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.billing.models import CreditTransaction, PurchaseRequest

logger = logging.getLogger(__name__)


@login_required
def planos(request):
    """Página de planos — mostra opções e saldo atual."""
    return render(request, "pages/planos.html", {
        "price_single": settings.PRICE_SINGLE_CENTS // 100,
        "pack_credits": settings.PACK_CREDITS,
        "pack_price": settings.PACK_PRICE_CENTS // 100,
        "whatsapp": settings.WHATSAPP_NUMBER,
        "balance": request.user.credit_balance(),
    })


@login_required
@require_POST
def comprar(request):
    """
    POST /planos/comprar/
    Cria PurchaseRequest com status PENDING e redireciona para o WhatsApp
    com a mensagem pré-preenchida.
    """
    plan = request.POST.get("plan", "")

    if plan == PurchaseRequest.PLAN_SINGLE:
        credits = 1
        price_cents = settings.PRICE_SINGLE_CENTS
        descricao = f"1 sorteio (R${settings.PRICE_SINGLE_CENTS // 100})"
    elif plan == PurchaseRequest.PLAN_PACK_30:
        credits = settings.PACK_CREDITS
        price_cents = settings.PACK_PRICE_CENTS
        descricao = f"Pacote {settings.PACK_CREDITS} sorteios (R${settings.PACK_PRICE_CENTS // 100})"
    else:
        return redirect("billing:planos")

    pr = PurchaseRequest.objects.create(
        user=request.user,
        plan=plan,
        credits=credits,
        price_cents=price_cents,
    )

    msg = (
        f"Olá! Quero {descricao}. "
        f"Conta: @{request.user.username} — Pedido #{pr.pk}"
    )
    wa_url = f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(msg)}"
    return redirect(wa_url)


@login_required
def conta(request):
    """Página 'Minha conta' — dados, extrato, pedidos, excluir conta."""
    transactions = CreditTransaction.objects.filter(
        user=request.user
    ).order_by("-created_at")[:30]

    pedidos = PurchaseRequest.objects.filter(
        user=request.user
    ).order_by("-created_at")[:10]

    try:
        ig_account = request.user.instagram_account
    except Exception:
        ig_account = None

    return render(request, "accounts/conta.html", {
        "balance": request.user.credit_balance(),
        "transactions": transactions,
        "pedidos": pedidos,
        "ig_account": ig_account,
    })


@login_required
@require_POST
def excluir_conta(request):
    """
    POST /conta/excluir/
    Remove dados pessoais do usuário (token, comentários, perfil IG).
    Mantém registros financeiros anonimizados (LGPD).
    """
    user = request.user

    try:
        account = user.instagram_account
        account._access_token = ""
        account.profile_picture_url = ""
        from django.utils import timezone as tz
        account.deauthorized_at = tz.now()
        account.save(update_fields=["_access_token", "profile_picture_url", "deauthorized_at"])
    except Exception:
        pass

    # Apaga snapshot de comentários
    from apps.raffles.models import RaffleComment
    RaffleComment.objects.filter(raffle__user=user).delete()

    # Desautentica e desativa a conta (mantém registros financeiros)
    from django.contrib.auth import logout
    logout(request)
    user.is_active = False
    user.username = f"excluido_{user.pk}"
    user.save(update_fields=["is_active", "username"])

    logger.info("Conta pk=%s excluída pelo próprio usuário.", user.pk)
    return redirect("pages:landing")
