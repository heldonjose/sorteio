from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.raffles.urls")),
    path("", include("apps.billing.urls")),
    path("", include("apps.pages.urls")),
]
