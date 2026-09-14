"""
Cria as PeriodicTask do django-celery-beat para este projeto.

Execute após cada deploy ou quando as tarefas periódicas forem alteradas:
    python manage.py setup_periodic_tasks
    # ou via Fabric:
    fab setup-tasks
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria/atualiza as PeriodicTask do django-celery-beat para o Sorteio Pro"

    def handle(self, *args, **options):
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        # ── Renovação diária de tokens ─────────────────────────────────────────
        daily, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="Renovar tokens do Instagram",
            defaults={
                "task": "apps.accounts.tasks.refresh_expiring_tokens",
                "interval": daily,
                "queue": "sorteio",
                "enabled": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("✓ PeriodicTask 'Renovar tokens do Instagram' criada.")
            )
        else:
            self.stdout.write("  PeriodicTask 'Renovar tokens do Instagram' já existe.")

        self.stdout.write(self.style.SUCCESS("\nTarefas periódicas configuradas com sucesso."))
