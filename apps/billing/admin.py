from django.contrib import admin
from django.utils import timezone
from .models import CreditTransaction, PurchaseRequest


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "kind", "price_brl", "raffle", "note", "created_by", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("user__username", "note")
    readonly_fields = (
        "user", "amount", "kind", "price_cents", "raffle",
        "purchase_request", "note", "created_by", "created_at",
    )
    ordering = ("-created_at",)

    @admin.display(description="Valor (R$)")
    def price_brl(self, obj):
        if obj.price_cents:
            return f"R${obj.price_cents / 100:.2f}".replace(".", ",")
        return "—"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.action(description="Marcar como pago e liberar créditos")
def mark_as_paid(modeladmin, request, queryset):
    count = 0
    for pr in queryset.filter(status=PurchaseRequest.STATUS_PENDING):
        kind = (
            CreditTransaction.KIND_PURCHASE_SINGLE
            if pr.plan == PurchaseRequest.PLAN_SINGLE
            else CreditTransaction.KIND_PURCHASE_PACK
        )
        CreditTransaction.objects.create(
            user=pr.user,
            amount=pr.credits,
            kind=kind,
            price_cents=pr.price_cents,
            purchase_request=pr,
            note=f"Pagamento aprovado — Pedido #{pr.pk}",
            created_by=request.user,
        )
        pr.status = PurchaseRequest.STATUS_PAID
        pr.paid_at = timezone.now()
        pr.approved_by = request.user
        pr.save(update_fields=["status", "paid_at", "approved_by"])
        count += 1

    modeladmin.message_user(request, f"{count} pedido(s) marcado(s) como pago e créditos liberados.")


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "price_brl", "credits", "status", "created_at", "paid_at")
    list_filter = ("status", "plan", "created_at")
    search_fields = ("user__username", "note")
    readonly_fields = ("user", "plan", "credits", "price_cents", "created_at", "updated_at")
    actions = [mark_as_paid]

    @admin.display(description="Valor")
    def price_brl(self, obj):
        return obj.price_brl
