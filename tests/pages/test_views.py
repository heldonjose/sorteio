import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPageViews:
    def test_landing_returns_200(self, client):
        url = reverse("pages:landing")
        response = client.get(url)
        assert response.status_code == 200

    def test_privacidade_returns_200(self, client):
        url = reverse("pages:privacidade")
        response = client.get(url)
        assert response.status_code == 200

    def test_termos_returns_200(self, client):
        url = reverse("pages:termos")
        response = client.get(url)
        assert response.status_code == 200

    def test_exclusao_dados_returns_200(self, client):
        url = reverse("pages:exclusao-dados")
        response = client.get(url)
        assert response.status_code == 200

    def test_landing_uses_correct_template(self, client):
        url = reverse("pages:landing")
        response = client.get(url)
        assert "pages/landing.html" in [t.name for t in response.templates]

    def test_landing_contains_instagram_cta(self, client):
        url = reverse("pages:landing")
        response = client.get(url)
        assert b"Instagram" in response.content

    def test_exclusao_dados_status_returns_200(self, client):
        url = reverse("pages:exclusao-dados-status", args=["abc123"])
        response = client.get(url)
        assert response.status_code == 200
        assert b"abc123" in response.content

    def test_exclusao_dados_status_mostra_codigo(self, client):
        code = "deadbeef1234567890abcdef"
        url = reverse("pages:exclusao-dados-status", args=[code])
        response = client.get(url)
        assert code.encode() in response.content

    def test_login_page_redireciona_usuario_logado(self, client, test_user):
        client.force_login(test_user)
        url = reverse("accounts:login")
        response = client.get(url)
        assert response.status_code == 302
        assert "/painel/" in response["Location"]

    def test_privacidade_contem_lgpd(self, client):
        response = client.get(reverse("pages:privacidade"))
        assert b"LGPD" in response.content

    def test_termos_contem_creditos(self, client):
        response = client.get(reverse("pages:termos"))
        assert "créditos".encode() in response.content
