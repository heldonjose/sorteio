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
