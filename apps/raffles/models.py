import uuid as _uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

from .algorithm import (
    CommentEntry,
    compute_participants_hash,
    filter_entries,
    sample_winners,
)


class Raffle(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_LOADING = "LOADING"
    STATUS_READY = "READY"
    STATUS_DRAWN = "DRAWN"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Rascunho"),
        (STATUS_LOADING, "Carregando comentários"),
        (STATUS_READY, "Pronto para sortear"),
        (STATUS_DRAWN, "Sorteado"),
        (STATUS_FAILED, "Falha"),
    ]

    uuid = models.UUIDField(default=_uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="raffles"
    )
    title = models.CharField(max_length=200, blank=True)

    # Snapshot do post
    ig_media_id = models.CharField(max_length=100, blank=True)
    permalink = models.TextField(blank=True)
    caption = models.TextField(blank=True)
    thumbnail_url = models.TextField(blank=True)
    media_type = models.CharField(max_length=20, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    comments_count = models.IntegerField(default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # Progresso de carregamento
    loaded_comments = models.IntegerField(default=0)
    load_started_at = models.DateTimeField(null=True, blank=True)
    load_finished_at = models.DateTimeField(null=True, blank=True)
    load_error = models.TextField(blank=True)

    # Regras do sorteio
    unique_per_user = models.BooleanField(default=True)
    include_replies = models.BooleanField(default=False)
    exclude_owner = models.BooleanField(default=True)
    min_mentions = models.IntegerField(default=0)
    required_keyword = models.CharField(max_length=200, blank=True)
    excluded_usernames = models.JSONField(default=list, blank=True)
    winners_count = models.IntegerField(default=1)
    alternates_count = models.IntegerField(default=0)
    comments_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    drawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Sorteio"
        verbose_name_plural = "Sorteios"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sorteio {self.uuid.hex[:8]} — @{self.user.username}"

    # ── Lógica de sorteio ────────────────────────────────────────────────────

    def _build_entries(self) -> list[CommentEntry]:
        return [
            CommentEntry(
                username=c.username,
                text=c.text,
                ig_comment_id=c.ig_comment_id,
                commented_at=c.commented_at,
                is_reply=c.is_reply,
                parent_ig_id=c.parent_ig_id,
            )
            for c in self.comments.all()
        ]

    def get_participants(self) -> list[CommentEntry]:
        """Retorna lista de participantes válidos com as regras do sorteio aplicadas."""
        try:
            owner_username = self.user.instagram_account.username
        except Exception:
            owner_username = ""

        return filter_entries(
            self._build_entries(),
            include_replies=self.include_replies,
            owner_username=owner_username,
            exclude_owner=self.exclude_owner,
            excluded_usernames=self.excluded_usernames or [],
            comments_until=self.comments_until,
            required_keyword=self.required_keyword,
            min_mentions=self.min_mentions,
            unique_per_user=self.unique_per_user,
        )

    def draw(self, reason: str = "") -> tuple["Draw", list["Winner"], list["Winner"]]:
        """
        Executa uma rodada de sorteio.
        - Na primeira rodada: debita 1 crédito e muda status para DRAWN.
        - Re-sorteios: gratuitos e registrados com motivo.
        Retorna (draw, ganhadores, suplentes).
        """
        from django.db import transaction
        from apps.billing.models import CreditTransaction

        participants = self.get_participants()

        if len(participants) < self.winners_count:
            raise ValueError(
                f"Participantes insuficientes: {len(participants)} disponíveis, "
                f"{self.winners_count} necessários."
            )

        participants_hash = compute_participants_hash(participants)
        winners_entries, alternates_entries = sample_winners(
            participants, self.winners_count, self.alternates_count
        )

        with transaction.atomic():
            is_first_draw = self.status != self.STATUS_DRAWN

            if is_first_draw:
                # Debita crédito com lock para evitar corrida
                user = (
                    self.__class__._default_manager
                    .select_for_update()
                    .get(pk=self.pk)
                    .user
                )
                balance = user.credit_balance()
                if balance < 1:
                    raise ValueError("Saldo insuficiente para realizar o sorteio.")

                CreditTransaction.objects.create(
                    user=self.user,
                    amount=-1,
                    kind="CONSUME",
                    raffle=self,
                    note="Sorteio realizado",
                )

            round_number = self.draws.count() + 1
            rules_snapshot = {
                "unique_per_user": self.unique_per_user,
                "include_replies": self.include_replies,
                "exclude_owner": self.exclude_owner,
                "min_mentions": self.min_mentions,
                "required_keyword": self.required_keyword,
                "excluded_usernames": self.excluded_usernames,
                "winners_count": self.winners_count,
                "alternates_count": self.alternates_count,
                "comments_until": self.comments_until.isoformat() if self.comments_until else None,
            }

            draw = Draw.objects.create(
                raffle=self,
                round=round_number,
                valid_entries=len(participants),
                participants_hash=participants_hash,
                rules_snapshot=rules_snapshot,
                random_source="secrets.SystemRandom",
                reason=reason,
            )

            winners: list[Winner] = []
            alternates: list[Winner] = []

            for i, entry in enumerate(winners_entries):
                w = Winner.objects.create(
                    draw=draw,
                    position=i + 1,
                    is_alternate=False,
                    username=entry.username,
                    comment_text=entry.text,
                    ig_comment_id=entry.ig_comment_id,
                    commented_at=entry.commented_at,
                )
                winners.append(w)

            for i, entry in enumerate(alternates_entries):
                a = Winner.objects.create(
                    draw=draw,
                    position=len(winners_entries) + i + 1,
                    is_alternate=True,
                    username=entry.username,
                    comment_text=entry.text,
                    ig_comment_id=entry.ig_comment_id,
                    commented_at=entry.commented_at,
                )
                alternates.append(a)

            if is_first_draw:
                self.status = self.STATUS_DRAWN
                self.drawn_at = timezone.now()
                self.save(update_fields=["status", "drawn_at"])

        return draw, winners, alternates


class RaffleComment(models.Model):
    """Snapshot dos comentários no momento do carregamento (apagado após 90 dias)."""

    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="comments")
    ig_comment_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    text = models.TextField()
    commented_at = models.DateTimeField()
    is_reply = models.BooleanField(default=False)
    parent_ig_id = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = [("raffle", "ig_comment_id")]
        indexes = [models.Index(fields=["raffle", "username"])]
        verbose_name = "Comentário do sorteio"
        verbose_name_plural = "Comentários do sorteio"

    def __str__(self):
        return f"@{self.username}: {self.text[:60]}"


class Draw(models.Model):
    """Cada rodada de sorteio (primeira ou re-sorteio)."""

    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="draws")
    round = models.IntegerField()
    valid_entries = models.IntegerField()
    participants_hash = models.CharField(max_length=64)
    rules_snapshot = models.JSONField(default=dict)
    random_source = models.CharField(max_length=100, default="secrets.SystemRandom")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("raffle", "round")]
        ordering = ["raffle", "round"]
        verbose_name = "Rodada de sorteio"
        verbose_name_plural = "Rodadas de sorteio"

    def __str__(self):
        return f"Rodada {self.round} — {self.raffle}"


class Winner(models.Model):
    """Ganhador ou suplente de uma rodada de sorteio."""

    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name="winners")
    position = models.IntegerField()
    is_alternate = models.BooleanField(default=False)
    username = models.CharField(max_length=100)
    comment_text = models.TextField()
    ig_comment_id = models.CharField(max_length=100)
    commented_at = models.DateTimeField()

    class Meta:
        unique_together = [("draw", "position")]
        ordering = ["draw", "position"]
        verbose_name = "Ganhador"
        verbose_name_plural = "Ganhadores"

    def __str__(self):
        label = "Suplente" if self.is_alternate else "Ganhador"
        return f"{label} #{self.position} — @{self.username}"
