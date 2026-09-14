import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-not-for-production")
os.environ.setdefault("DEBUG", "True")


@pytest.fixture
def test_user(db):
    from apps.accounts.models import User

    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def staff_user(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        username="admin", password="adminpass123", is_staff=True, is_superuser=True
    )


@pytest.fixture
def instagram_account(db, test_user, settings):
    from apps.accounts.models import InstagramAccount
    from django.utils import timezone
    from datetime import timedelta

    account = InstagramAccount(
        user=test_user,
        ig_user_id="123456789",
        username="testuser",
        name="Test User",
        token_expires_at=timezone.now() + timedelta(days=60),
    )
    account.access_token = "test-access-token"
    account.save()
    return account


@pytest.fixture
def raffle_with_comments(db, test_user, instagram_account):
    from apps.raffles.models import Raffle, RaffleComment
    from django.utils import timezone
    from datetime import timedelta

    raffle = Raffle.objects.create(
        user=test_user,
        ig_media_id="media_001",
        status="READY",
    )

    base = timezone.now() - timedelta(hours=5)
    comments_data = [
        ("alice", "Quero participar!", "c001", base + timedelta(minutes=1)),
        ("bob", "Eu também quero! @alice", "c002", base + timedelta(minutes=2)),
        ("carol", "Participando #sorteio @alice @bob", "c003", base + timedelta(minutes=3)),
        ("alice", "Segundo comentário da alice", "c004", base + timedelta(minutes=4)),
        ("dave", "Participando!", "c005", base + timedelta(minutes=5)),
    ]

    for username, text, comment_id, ts in comments_data:
        RaffleComment.objects.create(
            raffle=raffle,
            ig_comment_id=comment_id,
            username=username,
            text=text,
            commented_at=ts,
            is_reply=False,
        )

    return raffle
