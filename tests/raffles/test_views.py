"""
Testes de integração das views de sorteios.
"""
from unittest.mock import patch, MagicMock
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestPainel:
    def test_redirect_if_not_logged_in(self, client):
        url = reverse("raffles:painel")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/entrar/" in resp["Location"]

    def test_authenticated_user_sees_painel(self, client, test_user):
        client.force_login(test_user)
        resp = client.get(reverse("raffles:painel"))
        assert resp.status_code == 200
        assert "Painel" in resp.content.decode()

    def test_painel_shows_balance(self, client, test_user):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:painel"))
        assert "5" in resp.content.decode()


@pytest.mark.django_db
class TestHistorico:
    def test_lists_user_raffles(self, client, test_user):
        from apps.raffles.models import Raffle
        Raffle.objects.create(user=test_user, ig_media_id="m1", status="DRAWN")
        Raffle.objects.create(user=test_user, ig_media_id="m2", status="READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:historico"))
        assert resp.status_code == 200
        assert resp.context["raffles"].count() == 2

    def test_filters_by_status(self, client, test_user):
        from apps.raffles.models import Raffle
        Raffle.objects.create(user=test_user, ig_media_id="m1", status="DRAWN")
        Raffle.objects.create(user=test_user, ig_media_id="m2", status="READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:historico") + "?status=DRAWN")
        assert resp.context["raffles"].count() == 1

    def test_does_not_show_other_users_raffles(self, client, test_user, staff_user):
        from apps.raffles.models import Raffle
        Raffle.objects.create(user=staff_user, ig_media_id="m1", status="DRAWN")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:historico"))
        assert resp.context["raffles"].count() == 0


@pytest.mark.django_db
class TestNovo:
    def test_get_shows_form(self, client, test_user, instagram_account):
        with patch("apps.raffles.views._load_posts") as mock:
            mock.return_value = ([], "")
            client.force_login(test_user)
            resp = client.get(reverse("raffles:novo"))
        assert resp.status_code == 200

    def test_post_creates_raffle_and_redirects(self, client, test_user, instagram_account):
        from apps.raffles.models import Raffle
        client.force_login(test_user)

        with patch("apps.raffles.tasks.load_comments.delay") as mock_task:
            resp = client.post(reverse("raffles:novo"), {
                "ig_media_id": "media_123",
                "permalink": "https://instagram.com/p/abc",
                "caption": "Test post",
                "thumbnail_url": "",
                "media_type": "IMAGE",
            })

        assert resp.status_code == 302
        raffle = Raffle.objects.get(ig_media_id="media_123")
        assert raffle.user == test_user
        mock_task.assert_called_once_with(raffle.pk)
        assert f"/sorteios/{raffle.uuid}/carregar/" in resp["Location"]

    def test_post_without_media_id_shows_error(self, client, test_user, instagram_account):
        with patch("apps.raffles.views._load_posts", return_value=([], "")):
            client.force_login(test_user)
            resp = client.post(reverse("raffles:novo"), {"ig_media_id": ""})
        assert resp.status_code == 200
        assert "Selecione um post" in resp.content.decode()


@pytest.mark.django_db
class TestCarregar:
    def _make_raffle(self, user, status="LOADING"):
        from apps.raffles.models import Raffle
        return Raffle.objects.create(user=user, ig_media_id="m1", status=status)

    def test_shows_loading_page(self, client, test_user):
        raffle = self._make_raffle(test_user, "LOADING")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:carregar", args=[raffle.uuid]))
        assert resp.status_code == 200

    def test_redirects_to_regras_when_ready(self, client, test_user):
        raffle = self._make_raffle(test_user, "READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:carregar", args=[raffle.uuid]))
        assert resp.status_code == 302
        assert f"/sorteios/{raffle.uuid}/regras/" in resp["Location"]

    def test_returns_403_for_other_user(self, client, staff_user, test_user):
        raffle = self._make_raffle(staff_user)
        client.force_login(test_user)
        resp = client.get(reverse("raffles:carregar", args=[raffle.uuid]))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestRegras:
    def test_get_shows_rules_form(self, client, test_user, instagram_account):
        from apps.raffles.models import Raffle
        raffle = Raffle.objects.create(user=test_user, ig_media_id="m1", status="READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:regras", args=[raffle.uuid]))
        assert resp.status_code == 200
        assert "participantes" in resp.content.decode().lower()

    def test_post_saves_rules_and_redirects_to_sortear(self, client, test_user):
        from apps.raffles.models import Raffle
        raffle = Raffle.objects.create(user=test_user, ig_media_id="m1", status="READY")
        client.force_login(test_user)
        resp = client.post(reverse("raffles:regras", args=[raffle.uuid]), {
            "winners_count": "2",
            "alternates_count": "1",
            "unique_per_user": "on",
            "exclude_owner": "on",
            "min_mentions": "0",
            "required_keyword": "",
            "excluded_usernames": "",
        })
        assert resp.status_code == 302
        assert f"/sorteios/{raffle.uuid}/sortear/" in resp["Location"]
        raffle.refresh_from_db()
        assert raffle.winners_count == 2
        assert raffle.alternates_count == 1


@pytest.mark.django_db
class TestSortear:
    def test_get_shows_draw_page(self, client, test_user):
        from apps.raffles.models import Raffle
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=1, kind="FREE_GRANT")
        raffle = Raffle.objects.create(user=test_user, ig_media_id="m1", status="READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:sortear", args=[raffle.uuid]))
        assert resp.status_code == 200

    def test_post_executes_draw_and_redirects(self, client, test_user, raffle_with_comments):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT")
        client.force_login(test_user)
        resp = client.post(reverse("raffles:sortear", args=[raffle_with_comments.uuid]))
        assert resp.status_code == 302
        assert f"/sorteios/{raffle_with_comments.uuid}/" in resp["Location"]
        raffle_with_comments.refresh_from_db()
        assert raffle_with_comments.status == "DRAWN"

    def test_post_redirects_to_planos_without_credit(self, client, test_user, raffle_with_comments):
        client.force_login(test_user)
        resp = client.post(reverse("raffles:sortear", args=[raffle_with_comments.uuid]))
        assert resp.status_code == 302
        assert "/planos/" in resp["Location"]


@pytest.mark.django_db
class TestResultado:
    def test_shows_result_for_drawn_raffle(self, client, test_user, raffle_with_comments):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT")
        raffle_with_comments.draw()
        client.force_login(test_user)
        resp = client.get(reverse("raffles:resultado", args=[raffle_with_comments.uuid]))
        assert resp.status_code == 200
        assert "Resultado" in resp.content.decode()

    def test_redirects_if_not_drawn(self, client, test_user):
        from apps.raffles.models import Raffle
        raffle = Raffle.objects.create(user=test_user, ig_media_id="m1", status="READY")
        client.force_login(test_user)
        resp = client.get(reverse("raffles:resultado", args=[raffle.uuid]))
        assert resp.status_code == 302


@pytest.mark.django_db
class TestCertificado:
    def test_public_certificate_no_login(self, client, test_user, raffle_with_comments):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT")
        raffle_with_comments.draw()
        resp = client.get(reverse("raffles:certificado", args=[raffle_with_comments.uuid]))
        assert resp.status_code == 200
        assert "Certificado" in resp.content.decode()

    def test_returns_404_for_non_drawn_raffle(self, client, test_user):
        from apps.raffles.models import Raffle
        raffle = Raffle.objects.create(user=test_user, ig_media_id="m1", status="READY")
        resp = client.get(reverse("raffles:certificado", args=[raffle.uuid]))
        assert resp.status_code == 404
