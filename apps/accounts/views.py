import base64
import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.instagram.client import (
    InstagramAPIError,
    InstagramClient,
    exchange_code_for_short_token,
    exchange_for_long_token,
)

logger = logging.getLogger(__name__)

INSTAGRAM_OAUTH_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_SCOPES = "instagram_business_basic,instagram_business_manage_comments"


# ── Páginas de login / logout ─────────────────────────────────────────────────

def login_page(request):
    if request.user.is_authenticated:
        return redirect("raffles:painel")
    return render(request, "accounts/login.html")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("pages:landing")


# ── OAuth: authorize → callback ───────────────────────────────────────────────

def instagram_authorize(request):
    """Gera o state CSRF, salva na sessão e redireciona para o OAuth da Meta."""
    state = secrets.token_urlsafe(32)
    request.session["instagram_oauth_state"] = state

    params = {
        "client_id": settings.INSTAGRAM_APP_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": INSTAGRAM_SCOPES,
        "state": state,
    }
    return redirect(f"{INSTAGRAM_OAUTH_URL}?{urlencode(params)}")


def instagram_callback(request):
    """
    Callback da Meta após o usuário autorizar (ou negar) o acesso.
    Valida o state, troca o code pelos tokens, cria/atualiza User e InstagramAccount.
    """
    # ── Validação do state (proteção CSRF) ───────────────────────────────────
    state = request.GET.get("state", "")
    expected_state = request.session.pop("instagram_oauth_state", None)

    if not expected_state or not secrets.compare_digest(state, expected_state):
        return render(
            request,
            "accounts/error.html",
            {"message": "Erro de segurança (state inválido). Tente fazer login novamente."},
            status=400,
        )

    # ── Verificação de erro retornado pela Meta ───────────────────────────────
    if "error" in request.GET:
        error_desc = request.GET.get("error_description", "Acesso negado.")
        return render(request, "accounts/error.html", {"message": error_desc})

    # O code pode vir com sufixo "#_" — remover
    code = request.GET.get("code", "").split("#")[0]
    if not code:
        return render(request, "accounts/error.html", {"message": "Código de autorização ausente."})

    try:
        # ── Troca de tokens ───────────────────────────────────────────────────
        short_data = exchange_code_for_short_token(code, settings.INSTAGRAM_REDIRECT_URI)
        long_data = exchange_for_long_token(short_data["access_token"])

        access_token = long_data["access_token"]
        expires_in = long_data.get("expires_in", 5_184_000)  # 60 dias em segundos

        # ── Dados do perfil ───────────────────────────────────────────────────
        client = InstagramClient(access_token)
        me = client.get_me()

        ig_user_id = str(me["user_id"])
        username = me["username"]

        # ── Criar ou atualizar User ───────────────────────────────────────────
        from apps.accounts.models import User, InstagramAccount
        from apps.billing.models import CreditTransaction

        user, is_new = User.objects.get_or_create(
            ig_user_id=ig_user_id,
            defaults={"username": username},
        )

        if not is_new and user.username != username:
            # Usuário trocou @ no Instagram
            user.username = username
            user.save(update_fields=["username"])

        # ── Conceder créditos gratuitos (apenas na primeira vez) ──────────────
        if is_new:
            CreditTransaction.objects.create(
                user=user,
                amount=settings.FREE_RAFFLES_PER_ACCOUNT,
                kind=CreditTransaction.KIND_FREE_GRANT,
                note=f"{settings.FREE_RAFFLES_PER_ACCOUNT} sorteios gratuitos de boas-vindas",
            )

        # ── Criar ou atualizar InstagramAccount ───────────────────────────────
        account, _ = InstagramAccount.objects.get_or_create(
            user=user,
            defaults={"ig_user_id": ig_user_id, "username": username},
        )
        account.ig_user_id = ig_user_id
        account.username = me.get("username", username)
        account.name = me.get("name", "")
        account.profile_picture_url = me.get("profile_picture_url", "")
        account.account_type = me.get("account_type", "")
        account.media_count = me.get("media_count", 0)
        account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        account.last_refreshed_at = timezone.now()
        account.deauthorized_at = None
        account.access_token = access_token  # criptografado pela property
        account.save()

        # ── Login na sessão Django ────────────────────────────────────────────
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("raffles:painel")

    except InstagramAPIError as e:
        logger.error("InstagramAPIError no callback: %s (code=%s)", e, e.code)
        return render(
            request,
            "accounts/error.html",
            {"message": f"Erro ao conectar com o Instagram: {e}"},
        )
    except Exception as e:
        logger.exception("Erro inesperado no callback do Instagram")
        return render(
            request,
            "accounts/error.html",
            {"message": "Erro inesperado. Por favor, tente novamente."},
        )


# ── Callbacks obrigatórios da Meta ────────────────────────────────────────────

def _parse_signed_request(signed_request: str, app_secret: str) -> dict:
    """
    Valida e decodifica o signed_request da Meta (HMAC-SHA256).
    Lança ValueError se inválido.
    """
    try:
        encoded_sig, payload = signed_request.split(".")
    except ValueError:
        raise ValueError("Formato inválido de signed_request")

    sig = base64.urlsafe_b64decode(encoded_sig + "==")
    data = json.loads(base64.urlsafe_b64decode(payload + "=="))

    if data.get("algorithm", "").upper() != "HMAC-SHA256":
        raise ValueError(f"Algoritmo desconhecido: {data.get('algorithm')}")

    expected_sig = hmac.new(
        app_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Assinatura inválida no signed_request")

    return data


@csrf_exempt
@require_POST
def meta_deauthorize(request):
    """
    POST /meta/deauthorize/
    Meta notifica quando o usuário revoga o acesso ao app.
    Apaga o token e marca deauthorized_at.
    """
    try:
        signed_request = request.POST.get("signed_request", "")
        data = _parse_signed_request(signed_request, settings.INSTAGRAM_APP_SECRET)
        ig_user_id = str(data.get("user_id", ""))

        if ig_user_id:
            from apps.accounts.models import InstagramAccount

            try:
                account = InstagramAccount.objects.get(ig_user_id=ig_user_id)
                account._access_token = ""
                account.deauthorized_at = timezone.now()
                account.save(update_fields=["_access_token", "deauthorized_at"])
                logger.info("Conta @%s desautorizada via callback Meta.", account.username)
            except InstagramAccount.DoesNotExist:
                pass

        return JsonResponse({"success": True})

    except ValueError as e:
        logger.warning("meta_deauthorize: %s", e)
        return JsonResponse({"error": "Invalid signed_request"}, status=400)
    except Exception:
        logger.exception("Erro em meta_deauthorize")
        return JsonResponse({"error": "Internal error"}, status=500)


@csrf_exempt
@require_POST
def meta_data_deletion(request):
    """
    POST /meta/data-deletion/
    Meta notifica solicitação de exclusão de dados do usuário.
    Apaga dados pessoais e retorna URL de status + código de confirmação.
    """
    try:
        signed_request = request.POST.get("signed_request", "")
        data = _parse_signed_request(signed_request, settings.INSTAGRAM_APP_SECRET)
        ig_user_id = str(data.get("user_id", ""))

        confirmation_code = uuid.uuid4().hex

        if ig_user_id:
            from apps.accounts.models import InstagramAccount

            try:
                account = InstagramAccount.objects.get(ig_user_id=ig_user_id)
                account._access_token = ""
                account.profile_picture_url = ""
                account.deauthorized_at = timezone.now()
                account.save(update_fields=["_access_token", "profile_picture_url", "deauthorized_at"])

                # Apaga snapshot de comentários (dados pessoais de terceiros)
                from apps.raffles.models import RaffleComment
                RaffleComment.objects.filter(raffle__user=account.user).delete()

                logger.info(
                    "Exclusão de dados solicitada para ig_user_id=%s. Código: %s",
                    ig_user_id,
                    confirmation_code,
                )
            except InstagramAccount.DoesNotExist:
                pass

        return JsonResponse({
            "url": f"{settings.SITE_URL}/exclusao-de-dados/status/{confirmation_code}/",
            "confirmation_code": confirmation_code,
        })

    except ValueError as e:
        logger.warning("meta_data_deletion: %s", e)
        return JsonResponse({"error": "Invalid signed_request"}, status=400)
    except Exception:
        logger.exception("Erro em meta_data_deletion")
        return JsonResponse({"error": "Internal error"}, status=500)
