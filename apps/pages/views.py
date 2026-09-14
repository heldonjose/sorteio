from django.shortcuts import render, redirect


def landing(request):
    if request.user.is_authenticated:
        return redirect("raffles:painel")
    return render(request, "pages/landing.html")


def privacidade(request):
    return render(request, "pages/privacidade.html")


def termos(request):
    return render(request, "pages/termos.html")


def exclusao_dados(request):
    return render(request, "pages/exclusao_dados.html")


def planos(request):
    from django.conf import settings
    balance = request.user.credit_balance() if request.user.is_authenticated else 0
    return render(request, "pages/planos.html", {
        "price_single": settings.PRICE_SINGLE_CENTS // 100,
        "pack_credits": settings.PACK_CREDITS,
        "pack_price": settings.PACK_PRICE_CENTS // 100,
        "whatsapp": settings.WHATSAPP_NUMBER,
        "balance": balance,
    })


def exclusao_dados_status(request, confirmation_code):
    """
    Página de status da exclusão de dados solicitada via callback da Meta.
    A URL é retornada pelo endpoint POST /meta/data-deletion/ e pode ser
    verificada pelo revisor da Meta durante a Análise do App.
    """
    return render(request, "pages/exclusao_dados_status.html", {
        "confirmation_code": confirmation_code,
    })
