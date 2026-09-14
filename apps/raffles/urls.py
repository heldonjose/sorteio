from django.urls import path
from . import views

app_name = "raffles"

urlpatterns = [
    path("painel/",                              views.painel,                name="painel"),
    path("sorteios/",                            views.historico,             name="historico"),
    path("sorteios/novo/",                       views.novo,                  name="novo"),
    path("sorteios/posts/",                      views.posts_fragment,        name="posts_fragment"),
    path("sorteios/<uuid:uuid>/carregar/",       views.carregar,              name="carregar"),
    path("sorteios/<uuid:uuid>/progresso/",      views.progresso_fragment,    name="progresso"),
    path("sorteios/<uuid:uuid>/regras/",         views.regras,                name="regras"),
    path("sorteios/<uuid:uuid>/participantes/",  views.participantes_fragment, name="participantes"),
    path("sorteios/<uuid:uuid>/sortear/",        views.sortear,               name="sortear"),
    path("sorteios/<uuid:uuid>/",                views.resultado,             name="resultado"),
    path("r/<uuid:uuid>/",                       views.certificado,           name="certificado"),
]
