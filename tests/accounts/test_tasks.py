"""
Testes da tarefa Celery de renovação de tokens.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestRefreshExpiringTokens:
    def _make_account(self, db, test_user, days_until_expiry: int, last_refreshed_days_ago: int = 2):
        from apps.accounts.models import InstagramAccount

        account = InstagramAccount(
            user=test_user,
            ig_user_id=f"user_{days_until_expiry}_{last_refreshed_days_ago}",
            username=f"user_{days_until_expiry}",
            token_expires_at=timezone.now() + timedelta(days=days_until_expiry),
            last_refreshed_at=timezone.now() - timedelta(days=last_refreshed_days_ago),
        )
        account.access_token = "old-token"
        account.save()
        return account

    @patch("apps.accounts.tasks.refresh_long_token")
    def test_renews_token_expiring_soon(self, mock_refresh, db, test_user):
        from apps.accounts.tasks import refresh_expiring_tokens

        account = self._make_account(db, test_user, days_until_expiry=10)
        mock_refresh.return_value = {"access_token": "new-token", "expires_in": 5184000}

        result = refresh_expiring_tokens()

        assert result["refreshed"] == 1
        account.refresh_from_db()
        assert account.access_token == "new-token"

    @patch("apps.accounts.tasks.refresh_long_token")
    def test_skips_token_not_expiring_soon(self, mock_refresh, db, test_user):
        from apps.accounts.tasks import refresh_expiring_tokens

        self._make_account(db, test_user, days_until_expiry=30)
        result = refresh_expiring_tokens()

        assert result["refreshed"] == 0
        mock_refresh.assert_not_called()

    @patch("apps.accounts.tasks.refresh_long_token")
    def test_skips_recently_refreshed_token(self, mock_refresh, db, test_user):
        from apps.accounts.tasks import refresh_expiring_tokens

        # Token expira logo, mas foi renovado há 1h (< 24h)
        self._make_account(db, test_user, days_until_expiry=10, last_refreshed_days_ago=0)
        result = refresh_expiring_tokens()

        assert result["skipped"] == 1
        mock_refresh.assert_not_called()

    @patch("apps.accounts.tasks.refresh_long_token")
    def test_clears_token_on_api_error(self, mock_refresh, db, test_user):
        from apps.accounts.tasks import refresh_expiring_tokens
        from apps.instagram.client import InstagramAPIError

        account = self._make_account(db, test_user, days_until_expiry=5)
        mock_refresh.side_effect = InstagramAPIError("Token revogado", code=190)

        result = refresh_expiring_tokens()

        assert result["failed"] == 1
        account.refresh_from_db()
        assert account._access_token == ""

    @patch("apps.accounts.tasks.refresh_long_token")
    def test_skips_deauthorized_accounts(self, mock_refresh, db, test_user):
        from apps.accounts.tasks import refresh_expiring_tokens
        from apps.accounts.models import InstagramAccount

        account = self._make_account(db, test_user, days_until_expiry=5)
        account.deauthorized_at = timezone.now()
        account.save(update_fields=["deauthorized_at"])

        result = refresh_expiring_tokens()

        assert result["refreshed"] == 0
        mock_refresh.assert_not_called()
