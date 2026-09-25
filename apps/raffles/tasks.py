"""Tarefas Celery do app raffles."""

import logging

from celery import shared_task
from django.utils import timezone
from django.utils.translation import gettext_noop

from apps.instagram.client import InstagramAPIError, InstagramClient

logger = logging.getLogger(__name__)


@shared_task(name="apps.raffles.tasks.load_comments", bind=True, max_retries=3)
def load_comments(self, raffle_id: int) -> dict:
    """
    Carrega todos os comentários de um post do Instagram para o banco.

    - Atualiza `loaded_comments` a cada lote.
    - Marca status=READY ao concluir, FAILED em caso de erro sem retry.
    - Trata rate-limit com retry e backoff.
    """
    from apps.raffles.models import Raffle, RaffleComment

    try:
        raffle = Raffle.objects.get(pk=raffle_id)
    except Raffle.DoesNotExist:
        logger.error("load_comments: Raffle pk=%s não encontrado.", raffle_id)
        return {"error": "not_found"}

    raffle.status = Raffle.STATUS_LOADING
    raffle.load_started_at = timezone.now()
    raffle.load_finished_at = None
    raffle.load_error = ""
    raffle.loaded_comments = 0
    raffle.save(update_fields=["status", "load_started_at", "load_finished_at", "load_error", "loaded_comments"])

    try:
        access_token = raffle.user.instagram_account.access_token
    except Exception:
        # Guardado em português; traduzido na exibição ({% translate raffle.load_error %})
        _fail_raffle(raffle, gettext_noop("Conta do Instagram não encontrada ou token inválido."))
        return {"error": "no_token"}

    client = InstagramClient(access_token)
    total_loaded = 0
    after = None

    # Apaga comentários anteriores (re-carregamento)
    RaffleComment.objects.filter(raffle=raffle).delete()

    try:
        while True:
            try:
                page = client.get_comments(raffle.ig_media_id, after=after)
            except InstagramAPIError as e:
                if e.is_rate_limit:
                    countdown = 60 * (2 ** self.request.retries)
                    logger.warning("Rate-limit ao carregar comentários (raffle=%s). Retry em %ds.", raffle_id, countdown)
                    raise self.retry(exc=e, countdown=countdown)
                raise

            entries = page.get("data", [])
            batch = []

            for comment in entries:
                batch.append(RaffleComment(
                    raffle=raffle,
                    ig_comment_id=comment["id"],
                    username=comment.get("username", ""),
                    text=comment.get("text", ""),
                    commented_at=_parse_ts(comment.get("timestamp")),
                    is_reply=False,
                    parent_ig_id="",
                ))

                # Respostas aninhadas
                for reply in comment.get("replies", {}).get("data", []):
                    batch.append(RaffleComment(
                        raffle=raffle,
                        ig_comment_id=reply["id"],
                        username=reply.get("username", ""),
                        text=reply.get("text", ""),
                        commented_at=_parse_ts(reply.get("timestamp")),
                        is_reply=True,
                        parent_ig_id=comment["id"],
                    ))

            if batch:
                RaffleComment.objects.bulk_create(batch, ignore_conflicts=True)
                total_loaded += len(batch)
                raffle.loaded_comments = total_loaded
                raffle.save(update_fields=["loaded_comments"])

            # Paginação — seguir mesmo quando data vier vazio
            next_url = page.get("paging", {}).get("next")
            if not next_url:
                break

            cursors = page.get("paging", {}).get("cursors", {})
            after = cursors.get("after")
            if not after:
                break

        raffle.status = Raffle.STATUS_READY
        raffle.load_finished_at = timezone.now()
        raffle.save(update_fields=["status", "load_finished_at"])

        logger.info("load_comments concluído: raffle=%s, total=%d.", raffle_id, total_loaded)
        return {"loaded": total_loaded}

    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise
        _fail_raffle(raffle, str(exc))
        logger.exception("load_comments falhou definitivamente: raffle=%s.", raffle_id)
        return {"error": str(exc)}


def _fail_raffle(raffle, error: str) -> None:
    raffle.status = raffle.STATUS_FAILED
    raffle.load_error = error
    raffle.load_finished_at = timezone.now()
    raffle.save(update_fields=["status", "load_error", "load_finished_at"])


def _parse_ts(ts_str: str | None):
    """Converte timestamp ISO do Instagram para datetime com timezone."""
    if not ts_str:
        from django.utils import timezone as tz
        return tz.now()
    from django.utils.dateparse import parse_datetime
    from django.utils import timezone as tz
    dt = parse_datetime(ts_str)
    if dt and not dt.tzinfo:
        from django.utils.timezone import make_aware
        dt = make_aware(dt)
    return dt or tz.now()
