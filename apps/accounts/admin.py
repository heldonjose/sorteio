from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.conf import settings
from .models import User, InstagramAccount


# ── Inline de transações para o User ─────────────────────────────────────────

class CreditTransactionInline(admin.TabularInline):
    from apps.billing.models import CreditTransaction
    model = CreditTransaction
    fk_name = "user"
    extra = 0
    readonly_fields = ("amount", "kind", "price_cents", "raffle", "purchase_request", "note", "created_by", "created_at")
    can_delete = False
    show_change_link = False
    ordering = ("-created_at",)
    max_num = 20

    def has_add_permission(self, request, obj=None):
        return False


# ── Ações do admin para créditos ─────────────────────────────────────────────

@admin.action(description="Adicionar +1 sorteio (cortesia)")
def add_one_credit(modeladmin, request, queryset):
    from apps.billing.models import CreditTransaction

    for user in queryset:
        CreditTransaction.objects.create(
            user=user,
            amount=1,
            kind="ADJUST",
            note="Cortesia — 1 sorteio",
            created_by=request.user,
        )
    modeladmin.message_user(request, f"+1 crédito adicionado para {queryset.count()} usuário(s).")


@admin.action(description="Adicionar +30 sorteios (Pacote R$100)")
def add_pack_credits(modeladmin, request, queryset):
    from apps.billing.models import CreditTransaction

    for user in queryset:
        CreditTransaction.objects.create(
            user=user,
            amount=settings.PACK_CREDITS,
            kind="PURCHASE_PACK",
            price_cents=settings.PACK_PRICE_CENTS,
            note="Pacote 30 sorteios",
            created_by=request.user,
        )
    modeladmin.message_user(request, f"+{settings.PACK_CREDITS} créditos adicionados para {queryset.count()} usuário(s).")


@admin.action(description="Adicionar +1 sorteio avulso (R$10)")
def add_single_credit(modeladmin, request, queryset):
    from apps.billing.models import CreditTransaction

    for user in queryset:
        CreditTransaction.objects.create(
            user=user,
            amount=1,
            kind="PURCHASE_SINGLE",
            price_cents=settings.PRICE_SINGLE_CENTS,
            note="Compra avulsa — 1 sorteio",
            created_by=request.user,
        )
    modeladmin.message_user(request, f"+1 crédito (avulso) adicionado para {queryset.count()} usuário(s).")


# ── UserAdmin ─────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "ig_user_id", "get_credit_balance", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email", "ig_user_id")
    ordering = ("-date_joined",)
    actions = [add_one_credit, add_single_credit, add_pack_credits]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Instagram", {"fields": ("ig_user_id",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Instagram", {"fields": ("ig_user_id",)}),
    )

    inlines = [CreditTransactionInline]

    @admin.display(description="Saldo (sorteios)")
    def get_credit_balance(self, obj):
        return obj.credit_balance()


# ── InstagramAccountAdmin ─────────────────────────────────────────────────────

@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "account_type", "followers_count", "token_is_valid", "token_expires_at", "connected_at")
    list_filter = ("account_type",)
    search_fields = ("username", "ig_user_id", "user__username")
    readonly_fields = (
        "ig_user_id", "username", "name", "profile_picture_url", "account_type",
        "followers_count", "media_count", "token_expires_at", "permissions",
        "connected_at", "last_refreshed_at", "deauthorized_at",
    )
    exclude = ("_access_token",)

    @admin.display(description="Token válido", boolean=True)
    def token_is_valid(self, obj):
        return obj.token_is_valid

    def has_add_permission(self, request):
        return False
