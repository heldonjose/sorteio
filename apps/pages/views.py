from django.shortcuts import render


def landing(request):
    return render(request, "pages/landing.html")


def privacidade(request):
    return render(request, "pages/privacidade.html")


def termos(request):
    return render(request, "pages/termos.html")


def exclusao_dados(request):
    return render(request, "pages/exclusao_dados.html")
