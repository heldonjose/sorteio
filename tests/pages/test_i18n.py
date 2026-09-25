"""Idioma da interface: padrão pelo LANGUAGE_CODE, troca pelo seletor EN/PT (cookie)."""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestIdioma:
    def test_padrao_vem_do_language_code(self, client, settings):
        settings.LANGUAGE_CODE = "en"
        resp = client.get(reverse("pages:landing"))
        assert "Log in with Instagram" in resp.content.decode()
        assert resp["Content-Language"] == "en"

    def test_padrao_portugues(self, client, settings):
        settings.LANGUAGE_CODE = "pt-br"
        resp = client.get(reverse("pages:landing"))
        assert "Entrar com Instagram" in resp.content.decode()

    def test_ignora_accept_language_do_navegador(self, client, settings):
        settings.LANGUAGE_CODE = "en"
        resp = client.get(reverse("pages:landing"), HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9")
        assert "Log in with Instagram" in resp.content.decode()

    def test_seletor_grava_cookie_e_volta_para_pagina(self, client, settings):
        settings.LANGUAGE_CODE = "en"
        resp = client.post(reverse("set_language"), {"language": "pt-br", "next": "/termos/"})
        assert resp.status_code == 302
        assert resp["Location"] == "/termos/"
        assert resp.cookies[settings.LANGUAGE_COOKIE_NAME].value == "pt-br"
        resp = client.get(reverse("pages:landing"))
        assert "Entrar com Instagram" in resp.content.decode()

    def test_cookie_invalido_usa_padrao(self, client, settings):
        settings.LANGUAGE_CODE = "en"
        client.cookies[settings.LANGUAGE_COOKIE_NAME] = "xx"
        resp = client.get(reverse("pages:landing"))
        assert "Log in with Instagram" in resp.content.decode()

    def test_seletor_aparece_na_pagina(self, client):
        html = client.get(reverse("pages:landing")).content.decode()
        assert reverse("set_language") in html
        assert 'value="en"' in html and 'value="pt-br"' in html
