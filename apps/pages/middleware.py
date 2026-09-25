from django.conf import settings
from django.utils import translation


class DefaultLanguageMiddleware:
    """Ativa o idioma escolhido no seletor (cookie) ou, sem escolha, o LANGUAGE_CODE.

    Diferente do LocaleMiddleware do Django, ignora o Accept-Language do navegador:
    o idioma padrão é controlado só pela variável de ambiente LANGUAGE_CODE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if lang not in dict(settings.LANGUAGES):
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = translation.get_language()
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", request.LANGUAGE_CODE)
        return response
