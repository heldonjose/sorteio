from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Login / logout
    path("entrar/", views.login_page, name="login"),
    path("sair/", views.logout_view, name="logout"),

    # OAuth Instagram
    path("auth/instagram/authorize/", views.instagram_authorize, name="instagram-authorize"),
    path("auth/instagram/callback/", views.instagram_callback, name="instagram-callback"),

    # Callbacks obrigatórios da Meta
    path("meta/deauthorize/", views.meta_deauthorize, name="meta-deauthorize"),
    path("meta/data-deletion/", views.meta_data_deletion, name="meta-data-deletion"),
]
