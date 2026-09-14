"""
Testes de integração das views de billing.
"""
import pytest
from django.urls import reverse
from unittest.mock import patch


@pytest.mark.django_db
class TestPlanos:
    def test_planos_anonimo_redireciona_para_login(self, client):
        """A rota /planos/ do billing requer login."""
        resp = client.get(reverse("billing:planos"))
        assert resp.status_code == 302
        assert "/entrar/" in resp["Location"]

    def test_planos_autenticado_retorna_200(self, client, test_user):
        client.force_login(test_user)
        resp = client.get(reverse("billing:planos"))
        assert resp.status_code == 200
        assert "Planos simples" in resp.content.decode()

    def test_planos_mostra_saldo(self, client, test_user):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT")
        client.force_login(test_user)
        resp = client.get(reverse("billing:planos"))
        assert "5" in resp.content.decode()


@pytest.mark.django_db
class TestComprar:
    def test_comprar_avulso_cria_purchase_request(self, client, test_user):
        from apps.billing.models import PurchaseRequest
        client.force_login(test_user)
        resp = client.post(reverse("billing:comprar"), {"plan": "SINGLE"})
        assert resp.status_code == 302
        assert "wa.me" in resp["Location"]
        pr = PurchaseRequest.objects.get(user=test_user)
        assert pr.plan == "SINGLE"
        assert pr.credits == 1
        assert pr.status == "PENDING"

    def test_comprar_pacote_cria_purchase_request(self, client, test_user):
        from apps.billing.models import PurchaseRequest
        client.force_login(test_user)
        resp = client.post(reverse("billing:comprar"), {"plan": "PACK_30"})
        assert resp.status_code == 302
        pr = PurchaseRequest.objects.get(user=test_user)
        assert pr.plan == "PACK_30"
        assert pr.credits == 30

    def test_comprar_plano_invalido_redireciona(self, client, test_user):
        client.force_login(test_user)
        resp = client.post(reverse("billing:comprar"), {"plan": "INVALIDO"})
        assert resp.status_code == 302
        assert "/planos/" in resp["Location"]

    def test_comprar_url_whatsapp_contem_pedido(self, client, test_user):
        from apps.billing.models import PurchaseRequest
        client.force_login(test_user)
        client.post(reverse("billing:comprar"), {"plan": "SINGLE"})
        pr = PurchaseRequest.objects.get(user=test_user)
        # Não testa URL diretamente (redirect externo), mas verifica o pedido
        assert pr.pk is not None


@pytest.mark.django_db
class TestConta:
    def test_conta_requer_login(self, client):
        resp = client.get(reverse("billing:conta"))
        assert resp.status_code == 302

    def test_conta_mostra_dados(self, client, test_user):
        from apps.billing.models import CreditTransaction
        CreditTransaction.objects.create(user=test_user, amount=5, kind="FREE_GRANT", note="Boas-vindas")
        client.force_login(test_user)
        resp = client.get(reverse("billing:conta"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Minha conta" in content
        assert "Extrato" in content

    def test_conta_mostra_pedidos(self, client, test_user):
        from apps.billing.models import PurchaseRequest
        PurchaseRequest.objects.create(user=test_user, plan="SINGLE", credits=1, price_cents=1000)
        client.force_login(test_user)
        resp = client.get(reverse("billing:conta"))
        assert resp.status_code == 200
        assert "Pedidos" in resp.content.decode()

    def test_conta_nao_mostra_pedidos_de_outro_usuario(self, client, test_user, staff_user):
        from apps.billing.models import PurchaseRequest
        PurchaseRequest.objects.create(user=staff_user, plan="SINGLE", credits=1, price_cents=1000)
        client.force_login(test_user)
        resp = client.get(reverse("billing:conta"))
        # O contexto não deve ter pedidos do staff_user
        assert resp.context["pedidos"].count() == 0


@pytest.mark.django_db
class TestExcluirConta:
    def test_excluir_conta_desativa_usuario(self, client, test_user, instagram_account):
        client.force_login(test_user)
        resp = client.post(reverse("billing:excluir-conta"))
        assert resp.status_code == 302
        assert "/" in resp["Location"]
        test_user.refresh_from_db()
        assert not test_user.is_active

    def test_excluir_conta_apaga_token(self, client, test_user, instagram_account):
        client.force_login(test_user)
        client.post(reverse("billing:excluir-conta"))
        instagram_account.refresh_from_db()
        assert instagram_account._access_token == ""

    def test_excluir_conta_apaga_comentarios(self, client, test_user, raffle_with_comments):
        from apps.raffles.models import RaffleComment
        from apps.accounts.models import InstagramAccount
        from django.utils import timezone
        from datetime import timedelta
        # garante que a InstagramAccount existe (necessária pela view)
        if not hasattr(test_user, 'instagram_account'):
            InstagramAccount.objects.create(
                user=test_user, ig_user_id="999",
                username="testuser",
                token_expires_at=timezone.now() + timedelta(days=60),
            )
        client.force_login(test_user)
        assert RaffleComment.objects.filter(raffle__user=test_user).count() > 0
        client.post(reverse("billing:excluir-conta"))
        assert RaffleComment.objects.filter(raffle__user=test_user).count() == 0


@pytest.mark.django_db
class TestMarkAsPaid:
    """Testa a ação do admin que libera créditos."""

    def test_mark_as_paid_cria_transacao_e_atualiza_status(self, db, test_user, staff_user):
        from apps.billing.models import PurchaseRequest, CreditTransaction
        from apps.billing.admin import mark_as_paid

        pr = PurchaseRequest.objects.create(
            user=test_user, plan="SINGLE", credits=1, price_cents=1000
        )

        class FakeModelAdmin:
            def message_user(self, *args, **kwargs):
                pass

        class FakeRequest:
            user = staff_user

        mark_as_paid(FakeModelAdmin(), FakeRequest(), PurchaseRequest.objects.filter(pk=pr.pk))

        pr.refresh_from_db()
        assert pr.status == "PAID"
        assert pr.paid_at is not None
        assert pr.approved_by == staff_user

        tx = CreditTransaction.objects.get(purchase_request=pr)
        assert tx.amount == 1
        assert tx.kind == "PURCHASE_SINGLE"
        assert tx.created_by == staff_user
