"""
Comando para injetar comentários fictícios em um sorteio (uso em dev/teste).

Uso:
    python manage.py seed_comments <raffle_uuid> --count 100
    python manage.py seed_comments <raffle_uuid> --count 50 --mentions 2
"""
import random
import uuid as _uuid
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

USERNAMES = [
    "maria_silva", "joao_souza", "ana_costa", "pedro_lima", "julia_santos",
    "carlos_ferreira", "leticia_oliveira", "gabriel_rodrigues", "fernanda_alves",
    "lucas_martins", "camila_pereira", "rafael_gomes", "beatriz_carvalho",
    "matheus_ribeiro", "larissa_araujo", "diego_nascimento", "amanda_vieira",
    "thiago_mendes", "isabela_barbosa", "vinicius_rocha", "mariana_cavalcanti",
    "felipe_moura", "sabrina_pinto", "henrique_leal", "patricia_freitas",
    "rodrigo_nunes", "tatiana_medeiros", "eduardo_azevedo", "danielle_campos",
    "alexandre_moreira", "vanessa_teixeira", "leandro_cunha", "priscila_monteiro",
    "anderson_borges", "renata_cardoso", "fábio_correia", "elaine_duarte",
    "sergio_fonseca", "cintia_macedo", "marcelo_pires", "aline_ramos",
    "wellington_sousa", "claudia_xavier", "newton_braga", "simone_lacerda",
    "motivacancoes", "sandaliashelokids",
]

COMMENT_TEMPLATES = [
    "Quero participar! {mentions}",
    "Amei o produto! {mentions}",
    "Que sortudo eu serei 🙏 {mentions}",
    "Participando! {mentions}",
    "Adorei! {mentions}",
    "Dedos cruzados 🤞 {mentions}",
    "Muito legal! Já compartilhei! {mentions}",
    "Preciso muito disso! {mentions}",
    "Que promoção incrível! {mentions}",
    "Me lembrei de você {mentions}",
    "Manda o link {mentions}",
    "Que lindo! {mentions} olha isso!",
    "Já to participando {mentions}",
    "Sonho ter isso {mentions}",
    "Conta comigo! {mentions}",
]


class Command(BaseCommand):
    help = "Injeta comentários fictícios em um sorteio para testes"

    def add_arguments(self, parser):
        parser.add_argument("raffle_uuid", type=str, help="UUID do sorteio")
        parser.add_argument("--count", type=int, default=50, help="Número de comentários (padrão: 50)")
        parser.add_argument("--mentions", type=int, default=1, help="Menções por comentário (padrão: 1)")

    def handle(self, *args, **options):
        from apps.raffles.models import Raffle, RaffleComment

        try:
            raffle = Raffle.objects.get(uuid=options["raffle_uuid"])
        except Raffle.DoesNotExist:
            raise CommandError(f"Sorteio não encontrado: {options['raffle_uuid']}")

        count = options["count"]
        mentions_per = options["mentions"]

        # Apaga comentários anteriores
        deleted = RaffleComment.objects.filter(raffle=raffle).count()
        RaffleComment.objects.filter(raffle=raffle).delete()
        if deleted:
            self.stdout.write(f"  Removidos {deleted} comentários anteriores.")

        batch = []
        now = timezone.now()

        for i in range(count):
            username = random.choice(USERNAMES)
            mention_tags = " ".join(
                f"@{random.choice(USERNAMES)}" for _ in range(mentions_per)
            )
            text = random.choice(COMMENT_TEMPLATES).format(mentions=mention_tags).strip()

            batch.append(RaffleComment(
                raffle=raffle,
                ig_comment_id=f"fake_{_uuid.uuid4().hex}",
                username=username,
                text=text,
                commented_at=now,
                is_reply=False,
                parent_ig_id="",
            ))

        RaffleComment.objects.bulk_create(batch, ignore_conflicts=True)

        raffle.loaded_comments = count
        raffle.status = Raffle.STATUS_READY
        raffle.load_finished_at = now
        raffle.load_error = ""
        raffle.save(update_fields=["loaded_comments", "status", "load_finished_at", "load_error"])

        self.stdout.write(self.style.SUCCESS(
            f"✓ {count} comentários fictícios inseridos no sorteio {str(raffle.uuid)[:8]}."
        ))
        self.stdout.write(f"  Status → READY. Acesse: /sorteios/{raffle.uuid}/regras/")
