import pytest
from apps.billing.models import CreditTransaction
from apps.raffles.models import Raffle, RaffleComment, Draw, Winner


@pytest.mark.django_db
class TestRaffle:
    def test_create_raffle(self, test_user):
        raffle = Raffle.objects.create(user=test_user, ig_media_id="media_001")
        assert raffle.status == Raffle.STATUS_DRAFT
        assert raffle.uuid is not None

    def test_get_participants_unique_per_user(self, raffle_with_comments):
        raffle_with_comments.unique_per_user = True
        participants = raffle_with_comments.get_participants()
        usernames = [p.username for p in participants]
        # alice aparece duas vezes nos comentários mas só conta uma
        assert usernames.count("alice") == 1
        assert len(participants) == 4  # alice, bob, carol, dave

    def test_get_participants_all_entries(self, raffle_with_comments):
        raffle_with_comments.unique_per_user = False
        participants = raffle_with_comments.get_participants()
        assert len(participants) == 5  # todos os 5 comentários

    def test_get_participants_keyword_filter(self, raffle_with_comments):
        raffle_with_comments.required_keyword = "#sorteio"
        participants = raffle_with_comments.get_participants()
        # Só carol tem #sorteio no texto
        assert len(participants) == 1
        assert participants[0].username == "carol"

    def test_get_participants_min_mentions(self, raffle_with_comments):
        raffle_with_comments.min_mentions = 2
        participants = raffle_with_comments.get_participants()
        # carol tem @alice @bob = 2 menções distintas
        assert len(participants) == 1
        assert participants[0].username == "carol"

    def test_str(self, raffle_with_comments):
        assert "testuser" in str(raffle_with_comments)


@pytest.mark.django_db
class TestRaffleDraw:
    def _setup_balance(self, user, amount=5):
        CreditTransaction.objects.create(
            user=user,
            amount=amount,
            kind=CreditTransaction.KIND_FREE_GRANT,
            note="Setup teste",
        )

    def test_draw_creates_draw_and_winners(self, raffle_with_comments, test_user):
        self._setup_balance(test_user)
        draw, winners, alternates = raffle_with_comments.draw()

        assert draw is not None
        assert draw.round == 1
        assert len(winners) == 1
        assert len(alternates) == 0

    def test_draw_debits_credit(self, raffle_with_comments, test_user):
        self._setup_balance(test_user, 5)
        raffle_with_comments.draw()
        assert test_user.credit_balance() == 4

    def test_draw_changes_status_to_drawn(self, raffle_with_comments, test_user):
        self._setup_balance(test_user)
        raffle_with_comments.draw()
        raffle_with_comments.refresh_from_db()
        assert raffle_with_comments.status == Raffle.STATUS_DRAWN

    def test_redraw_is_free(self, raffle_with_comments, test_user):
        self._setup_balance(test_user, 1)
        raffle_with_comments.draw()
        balance_after_first = test_user.credit_balance()

        raffle_with_comments.draw(reason="Ganhador não se qualificou")
        balance_after_redraw = test_user.credit_balance()

        assert balance_after_first == balance_after_redraw  # re-sorteio gratuito

    def test_redraw_increments_round(self, raffle_with_comments, test_user):
        self._setup_balance(test_user)
        raffle_with_comments.draw()
        raffle_with_comments.draw(reason="Re-sorteio")
        assert raffle_with_comments.draws.count() == 2
        assert raffle_with_comments.draws.last().round == 2

    def test_draw_fails_without_credit(self, raffle_with_comments):
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            raffle_with_comments.draw()

    def test_draw_fails_with_insufficient_participants(self, test_user, instagram_account):
        from apps.billing.models import CreditTransaction

        raffle = Raffle.objects.create(
            user=test_user,
            ig_media_id="media_empty",
            status=Raffle.STATUS_READY,
            winners_count=5,
        )
        CreditTransaction.objects.create(user=test_user, amount=5, kind=CreditTransaction.KIND_FREE_GRANT)

        with pytest.raises(ValueError, match="Participantes insuficientes"):
            raffle.draw()

    def test_draw_records_participants_hash(self, raffle_with_comments, test_user):
        self._setup_balance(test_user)
        draw, _, _ = raffle_with_comments.draw()
        assert len(draw.participants_hash) == 64

    def test_draw_records_rules_snapshot(self, raffle_with_comments, test_user):
        self._setup_balance(test_user)
        draw, _, _ = raffle_with_comments.draw()
        assert "unique_per_user" in draw.rules_snapshot
