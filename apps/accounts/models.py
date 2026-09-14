from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum


class User(AbstractUser):
    """
    Usuário da plataforma.
    - Usuários comuns: fazem login via Instagram OAuth (ig_user_id preenchido).
    - Admins: is_staff=True, login pela URL do Django Admin (ig_user_id nulo).
    """

    ig_user_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True,
        verbose_name="Instagram user ID",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def credit_balance(self) -> int:
        from apps.billing.models import CreditTransaction

        result = CreditTransaction.objects.filter(user=self).aggregate(total=Sum("amount"))
        return result["total"] or 0

    credit_balance.short_description = "Saldo"

    def __str__(self):
        return self.username


class InstagramAccount(models.Model):
    """Dados da conta profissional do Instagram vinculada ao usuário."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="instagram_account"
    )
    ig_user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=200, blank=True)
    profile_picture_url = models.URLField(max_length=500, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    followers_count = models.IntegerField(default=0)
    media_count = models.IntegerField(default=0)

    # Token armazenado criptografado com Fernet (coluna no banco: access_token)
    _access_token = models.TextField(db_column="access_token", blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    permissions = models.JSONField(default=list, blank=True)

    connected_at = models.DateTimeField(auto_now_add=True)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    deauthorized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Conta do Instagram"
        verbose_name_plural = "Contas do Instagram"

    # ── Criptografia transparente do token ─────────────────────────────────

    @property
    def access_token(self) -> str:
        from .encryption import decrypt

        return decrypt(self._access_token) if self._access_token else ""

    @access_token.setter
    def access_token(self, value: str):
        from .encryption import encrypt

        self._access_token = encrypt(value) if value else ""

    @property
    def token_is_valid(self) -> bool:
        if not self._access_token or not self.token_expires_at:
            return False
        from django.utils import timezone

        return self.token_expires_at > timezone.now()

    token_is_valid.fget.short_description = "Token válido"

    def __str__(self):
        return f"@{self.username}"
