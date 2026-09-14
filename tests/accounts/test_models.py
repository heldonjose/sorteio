import pytest
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestUser:
    def test_create_user(self, test_user):
        assert test_user.username == "testuser"
        assert test_user.ig_user_id is None

    def test_credit_balance_zero_new_user(self, test_user):
        assert test_user.credit_balance() == 0

    def test_credit_balance_after_grant(self, test_user):
        from apps.billing.models import CreditTransaction

        CreditTransaction.objects.create(
            user=test_user,
            amount=5,
            kind=CreditTransaction.KIND_FREE_GRANT,
            note="Boas-vindas",
        )
        assert test_user.credit_balance() == 5

    def test_credit_balance_after_debit(self, test_user):
        from apps.billing.models import CreditTransaction

        CreditTransaction.objects.create(user=test_user, amount=5, kind=CreditTransaction.KIND_FREE_GRANT)
        CreditTransaction.objects.create(user=test_user, amount=-1, kind=CreditTransaction.KIND_CONSUME)
        assert test_user.credit_balance() == 4

    def test_credit_balance_cannot_go_negative_via_model(self, test_user):
        """O modelo em si não impede saldo negativo — isso é responsabilidade do draw()."""
        from apps.billing.models import CreditTransaction

        CreditTransaction.objects.create(user=test_user, amount=-3, kind=CreditTransaction.KIND_CONSUME)
        assert test_user.credit_balance() == -3


@pytest.mark.django_db
class TestInstagramAccount:
    def test_token_encrypt_decrypt(self, instagram_account):
        # O token armazenado no banco é diferente do token em texto claro
        assert instagram_account._access_token != "test-access-token"
        assert instagram_account.access_token == "test-access-token"

    def test_token_is_valid_when_not_expired(self, instagram_account):
        assert instagram_account.token_is_valid is True

    def test_token_is_invalid_when_expired(self, db, test_user, settings):
        from apps.accounts.models import InstagramAccount

        account = InstagramAccount(
            user=test_user,
            ig_user_id="expired_001",
            username="expireduser",
            token_expires_at=timezone.now() - timedelta(days=1),
        )
        account.access_token = "expired-token"
        account.save()
        assert account.token_is_valid is False

    def test_token_is_invalid_when_empty(self, db, test_user):
        from apps.accounts.models import InstagramAccount

        account = InstagramAccount.objects.create(
            user=test_user,
            ig_user_id="notoken_001",
            username="notokenuser",
        )
        assert account.token_is_valid is False

    def test_str(self, instagram_account):
        assert str(instagram_account) == "@testuser"
