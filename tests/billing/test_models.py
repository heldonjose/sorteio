import pytest
from apps.billing.models import CreditTransaction, PurchaseRequest


@pytest.mark.django_db
class TestCreditTransaction:
    def test_create_free_grant(self, test_user):
        tx = CreditTransaction.objects.create(
            user=test_user,
            amount=5,
            kind=CreditTransaction.KIND_FREE_GRANT,
            note="Boas-vindas",
        )
        assert tx.amount == 5
        assert tx.kind == CreditTransaction.KIND_FREE_GRANT
        assert tx.created_at is not None

    def test_ledger_accumulates(self, test_user):
        CreditTransaction.objects.create(user=test_user, amount=5, kind=CreditTransaction.KIND_FREE_GRANT)
        CreditTransaction.objects.create(user=test_user, amount=30, kind=CreditTransaction.KIND_PURCHASE_PACK, price_cents=10000)
        CreditTransaction.objects.create(user=test_user, amount=-1, kind=CreditTransaction.KIND_CONSUME)
        assert test_user.credit_balance() == 34

    def test_str_positive(self, test_user):
        tx = CreditTransaction.objects.create(user=test_user, amount=5, kind=CreditTransaction.KIND_FREE_GRANT)
        assert "+5" in str(tx)

    def test_str_negative(self, test_user):
        tx = CreditTransaction.objects.create(user=test_user, amount=-1, kind=CreditTransaction.KIND_CONSUME)
        assert "-1" in str(tx)


@pytest.mark.django_db
class TestPurchaseRequest:
    def test_create_pending(self, test_user):
        pr = PurchaseRequest.objects.create(
            user=test_user,
            plan=PurchaseRequest.PLAN_SINGLE,
            credits=1,
            price_cents=1000,
        )
        assert pr.status == PurchaseRequest.STATUS_PENDING
        assert pr.paid_at is None

    def test_price_brl(self, test_user):
        pr = PurchaseRequest.objects.create(
            user=test_user,
            plan=PurchaseRequest.PLAN_PACK_30,
            credits=30,
            price_cents=10000,
        )
        assert pr.price_brl == "R$100,00"

    def test_str(self, test_user):
        pr = PurchaseRequest.objects.create(
            user=test_user,
            plan=PurchaseRequest.PLAN_SINGLE,
            credits=1,
            price_cents=1000,
        )
        assert "testuser" in str(pr)
