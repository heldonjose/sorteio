from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("planos/",          views.planos,        name="planos"),
    path("planos/comprar/",  views.comprar,       name="comprar"),
    path("conta/",           views.conta,         name="conta"),
    path("conta/excluir/",   views.excluir_conta, name="excluir-conta"),
]
