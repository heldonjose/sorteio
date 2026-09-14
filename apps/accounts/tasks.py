import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.accounts.tasks.refresh_expiring_tokens")
def refresh_expiring_tokens():
    """
    Renova tokens do Instagram que expiram em menos de 15 dias.
    Executada diariamente via django-celery-beat (setup_periodic_tasks).

    Regra: token com mais de 24h de vida e que expira em < 15 dias.
    Se falhar, o token é apagado e o usuário precisará fazer login novamente.
    """
    from apps.accounts.models import InstagramAccount
    from apps.instagram.client import InstagramAPIError, refresh_long_token

    soon = timezone.now() + timedelta(days=15)
    min_age_threshold = timezone.now() - timedelta(hours=24)

    accounts = InstagramAccount.objects.filter(
        token_expires_at__lt=soon,
        deauthorized_at__isnull=True,
    ).exclude(_access_token="")

    refreshed = 0
    skipped = 0
    failed = 0

    for account in accounts:
        # Pula se foi renovado nas últimas 24h
        if account.last_refreshed_at and account.last_refreshed_at > min_age_threshold:
            skipped += 1
            continue

        try:
            result = refresh_long_token(account.access_token)
            account.access_token = result["access_token"]
            expires_in = result.get("expires_in", 5_184_000)  # 60 dias padrão
            account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            account.last_refreshed_at = timezone.now()
            account.save(update_fields=["_access_token", "token_expires_at", "last_refreshed_at"])
            refreshed += 1
            logger.info("Token renovado para @%s (expira em %s dias).", account.username, expires_in // 86400)

        except InstagramAPIError as e:
            logger.warning("Falha ao renovar token para @%s: %s (code=%s)", account.username, e, e.code)
            # Token inválido ou acesso revogado — limpa o token para forçar novo login
            account._access_token = ""
            account.save(update_fields=["_access_token"])
            failed += 1

        except Exception:
            logger.exception("Erro inesperado ao renovar token para @%s", account.username)
            failed += 1

    logger.info(
        "refresh_expiring_tokens concluído: %d renovados, %d ignorados, %d com falha.",
        refreshed, skipped, failed,
    )
    return {"refreshed": refreshed, "skipped": skipped, "failed": failed}
