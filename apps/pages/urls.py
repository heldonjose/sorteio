from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("privacidade/", views.privacidade, name="privacidade"),
    path("termos/", views.termos, name="termos"),
    path("exclusao-de-dados/", views.exclusao_dados, name="exclusao-dados"),
]
