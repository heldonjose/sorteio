from django.conf import settings


def app_settings(request):
    """Injeta configurações globais do produto em todos os templates."""
    return {
        "APP_NAME": settings.APP_NAME,
    }
