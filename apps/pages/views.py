from django.shortcuts import render


def landing(request):
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
