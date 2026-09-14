from django.conf import settings
from django.db import models
from django.db.models import Sum


class CreditTransaction(models.Model):
    """
    Livro-razão de créditos — imutável.
    Saldo = Sum('amount') filtrando por usuário.
    Nunca editar/deletar linhas existentes.
    """

    KIND_FREE_GRANT = "FREE_GRANT"
    KIND_PURCHASE_SINGLE = "PURCHASE_SINGLE"
    KIND_PURCHASE_PACK = "PURCHASE_PACK"
    KIND_CONSUME = "CONSUME"
    KIND_ADJUST = "ADJUST"
    KIND_REFUND = "REFUND"

    KIND_CHOICES = [
        (KIND_FREE_GRANT, "Créditos gratuitos (boas-vindas)"),
        (KIND_PURCHASE_SINGLE, "Compra avulsa — 1 sorteio"),
        (KIND_PURCHASE_PACK, "Compra pacote — 30 sorteios"),
        (KIND_CONSUME, "Uso em sorteio"),
        (KIND_ADJUST, "Ajuste / cortesia"),
        (KIND_REFUND, "Estorno"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_transactions",
    )
    amount = models.IntegerField(help_text="Positivo = crédito; negativo = débito")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    price_cents = models.IntegerField(null=True, blank=True, help_text="Valor pago em centavos (apenas em compras)")
    raffle = models.ForeignKey(
        "raffles.Raffle",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="credit_transactions",
    )
    purchase_request = models.ForeignKey(
        "PurchaseRequest",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_credit_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transação de crédito"
        verbose_name_plural = "Transações de crédito"
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{sign}{self.amount} ({self.get_kind_display()}) — @{self.user.username}"


class PurchaseRequest(models.Model):
    """Pedido de compra de créditos via WhatsApp."""

    PLAN_SINGLE = "SINGLE"
    PLAN_PACK_30 = "PACK_30"
    PLAN_CHOICES = [
        (PLAN_SINGLE, "Avulso — 1 sorteio (R$10)"),
        (PLAN_PACK_30, "Pacote — 30 sorteios (R$100)"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_CANCELED = "CANCELED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Aguardando pagamento"),
        (STATUS_PAID, "Pago e liberado"),
        (STATUS_CANCELED, "Cancelado"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchase_requests",
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    credits = models.IntegerField()
    price_cents = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_purchases",
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido de compra"
        verbose_name_plural = "Pedidos de compra"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{self.pk} — @{self.user.username} ({self.get_plan_display()})"

    @property
    def price_brl(self) -> str:
        return f"R${self.price_cents / 100:.2f}".replace(".", ",")
