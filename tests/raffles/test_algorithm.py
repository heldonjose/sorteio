"""
Testes unitários do algoritmo de sorteio — sem banco de dados.
"""

from datetime import datetime, timezone as dt_tz
from apps.raffles.algorithm import (
    CommentEntry,
    count_distinct_mentions,
    filter_entries,
    compute_participants_hash,
    sample_winners,
)


def make_entry(username: str, text: str, comment_id: str, minutes_offset: int = 0, is_reply: bool = False) -> CommentEntry:
    base = datetime(2026, 1, 1, 12, 0, tzinfo=dt_tz.utc)
    from datetime import timedelta
    return CommentEntry(
        username=username,
        text=text,
        ig_comment_id=comment_id,
        commented_at=base + timedelta(minutes=minutes_offset),
        is_reply=is_reply,
    )


class TestCountDistinctMentions:
    def test_no_mentions(self):
        assert count_distinct_mentions("Oi, quero participar!", "alice") == 0

    def test_one_mention(self):
        assert count_distinct_mentions("Confira @bob!", "alice") == 1

    def test_two_distinct_mentions(self):
        assert count_distinct_mentions("@bob @carol participem!", "alice") == 2

    def test_excludes_author(self):
        assert count_distinct_mentions("@alice @bob", "alice") == 1

    def test_author_case_insensitive(self):
        assert count_distinct_mentions("@Alice @bob", "alice") == 1

    def test_duplicate_mentions_counted_once(self):
        assert count_distinct_mentions("@bob e @bob de novo", "alice") == 1

    def test_strips_punctuation(self):
        assert count_distinct_mentions("@bob, @carol.", "alice") == 2


class TestFilterEntries:
    def _default_kwargs(self, **overrides):
        defaults = dict(
            include_replies=False,
            owner_username="owner",
            exclude_owner=True,
            excluded_usernames=[],
            comments_until=None,
            required_keyword="",
            min_mentions=0,
            unique_per_user=True,
        )
        defaults.update(overrides)
        return defaults

    def test_basic_filter_no_rules(self):
        entries = [
            make_entry("alice", "Participando", "c1", 1),
            make_entry("bob", "Participando", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs())
        assert len(result) == 2

    def test_excludes_replies(self):
        entries = [
            make_entry("alice", "Comentário", "c1", 1, is_reply=False),
            make_entry("bob", "Resposta", "c2", 2, is_reply=True),
        ]
        result = filter_entries(entries, **self._default_kwargs(include_replies=False))
        assert len(result) == 1
        assert result[0].username == "alice"

    def test_includes_replies_when_configured(self):
        entries = [
            make_entry("alice", "Comentário", "c1", 1, is_reply=False),
            make_entry("bob", "Resposta", "c2", 2, is_reply=True),
        ]
        result = filter_entries(entries, **self._default_kwargs(include_replies=True))
        assert len(result) == 2

    def test_excludes_owner(self):
        entries = [
            make_entry("owner", "Meu post", "c1", 1),
            make_entry("alice", "Participando", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs(owner_username="owner", exclude_owner=True))
        assert len(result) == 1
        assert result[0].username == "alice"

    def test_excludes_custom_usernames(self):
        entries = [
            make_entry("spammer", "Spam", "c1", 1),
            make_entry("alice", "Ok", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs(excluded_usernames=["spammer"]))
        assert len(result) == 1

    def test_required_keyword(self):
        entries = [
            make_entry("alice", "Quero participar #sorteio", "c1", 1),
            make_entry("bob", "Só comentando", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs(required_keyword="#sorteio"))
        assert len(result) == 1
        assert result[0].username == "alice"

    def test_required_keyword_case_insensitive(self):
        entries = [make_entry("alice", "Quero #SORTEIO", "c1", 1)]
        result = filter_entries(entries, **self._default_kwargs(required_keyword="#sorteio"))
        assert len(result) == 1

    def test_min_mentions(self):
        entries = [
            make_entry("alice", "Venha @bob @carol!", "c1", 1),
            make_entry("dave", "Participando", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs(min_mentions=2))
        assert len(result) == 1
        assert result[0].username == "alice"

    def test_unique_per_user_keeps_first(self):
        entries = [
            make_entry("alice", "Primeiro", "c1", 1),
            make_entry("alice", "Segundo", "c2", 2),
        ]
        result = filter_entries(entries, **self._default_kwargs(unique_per_user=True))
        assert len(result) == 1
        assert result[0].ig_comment_id == "c1"

    def test_comments_until_filter(self):
        from datetime import timedelta
        base = datetime(2026, 1, 1, 12, 0, tzinfo=dt_tz.utc)
        entries = [
            make_entry("alice", "Cedo", "c1", 1),
            make_entry("bob", "Tarde", "c2", 120),
        ]
        cutoff = base + timedelta(minutes=60)
        result = filter_entries(entries, **self._default_kwargs(comments_until=cutoff))
        assert len(result) == 1
        assert result[0].username == "alice"

    def test_deterministic_ordering(self):
        entries = [
            make_entry("bob", "B", "c2", 2),
            make_entry("alice", "A", "c1", 1),
        ]
        result = filter_entries(entries, **self._default_kwargs(unique_per_user=False))
        assert result[0].username == "alice"
        assert result[1].username == "bob"


class TestComputeParticipantsHash:
    def test_same_participants_same_hash(self):
        entries = [make_entry("alice", "A", "c1", 1), make_entry("bob", "B", "c2", 2)]
        h1 = compute_participants_hash(entries)
        h2 = compute_participants_hash(entries)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_different_participants_different_hash(self):
        entries1 = [make_entry("alice", "A", "c1", 1)]
        entries2 = [make_entry("bob", "B", "c2", 2)]
        assert compute_participants_hash(entries1) != compute_participants_hash(entries2)


class TestSampleWinners:
    def test_single_winner(self):
        entries = [make_entry(f"user{i}", "text", f"c{i}", i) for i in range(10)]
        winners, alternates = sample_winners(entries, winners_count=1, alternates_count=0)
        assert len(winners) == 1
        assert len(alternates) == 0

    def test_winners_and_alternates(self):
        entries = [make_entry(f"user{i}", "text", f"c{i}", i) for i in range(10)]
        winners, alternates = sample_winners(entries, winners_count=2, alternates_count=3)
        assert len(winners) == 2
        assert len(alternates) == 3

    def test_no_duplicate_winners(self):
        entries = [make_entry(f"user{i}", "text", f"c{i}", i) for i in range(5)]
        winners, alternates = sample_winners(entries, winners_count=3, alternates_count=2)
        all_chosen = winners + alternates
        usernames = [e.username for e in all_chosen]
        assert len(usernames) == len(set(usernames))

    def test_fewer_participants_than_requested(self):
        entries = [make_entry(f"user{i}", "text", f"c{i}", i) for i in range(3)]
        winners, alternates = sample_winners(entries, winners_count=2, alternates_count=5)
        # Máximo possível é 3
        assert len(winners) + len(alternates) == 3

    def test_empty_participants(self):
        winners, alternates = sample_winners([], winners_count=1, alternates_count=0)
        assert winners == []
        assert alternates == []
