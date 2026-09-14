"""
Cliente para a Instagram API with Instagram Login (Business Login).
Documentação: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login
"""

import requests
from django.conf import settings

BASE_GRAPH_URL = "https://graph.instagram.com"
BASE_AUTH_URL = "https://api.instagram.com"


class InstagramAPIError(Exception):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code

    @property
    def is_rate_limit(self) -> bool:
        return self.code in (4, 17, 32, 613)


class InstagramClient:
    """Cliente autenticado com o access_token de um usuário."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.api_version = settings.INSTAGRAM_API_VERSION

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{BASE_GRAPH_URL}/{self.api_version}/{endpoint}"
        p = {"access_token": self.access_token}
        if params:
            p.update(params)
        response = requests.get(url, params=p, timeout=30)
        data = response.json()
        if "error" in data:
            raise InstagramAPIError(
                data["error"].get("message", "Unknown error"),
                code=data["error"].get("code"),
            )
        return data

    def get_me(self) -> dict:
        """Retorna dados do perfil do usuário autenticado."""
        return self._get(
            "me",
            {"fields": "user_id,username,name,profile_picture_url,account_type,media_count"},
        )

    def get_media(self, after: str | None = None) -> dict:
        """Lista posts do usuário (24 por página)."""
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count",
            "limit": 24,
        }
        if after:
            params["after"] = after
        return self._get("me/media", params)

    def get_comments(self, media_id: str, after: str | None = None) -> dict:
        """
        Lista comentários de uma publicação.
        Atenção: em modo desenvolvimento retorna páginas vazias — normal.
        Siga paging.next mesmo quando data vier vazio.
        """
        params = {
            "fields": "id,text,username,timestamp,replies{id,text,username,timestamp}",
            "limit": 50,
        }
        if after:
            params["after"] = after
        return self._get(f"{media_id}/comments", params)


# ── Funções de OAuth ──────────────────────────────────────────────────────────

def exchange_code_for_short_token(code: str, redirect_uri: str) -> dict:
    """Troca o authorization code pelo token curto (válido por 1h)."""
    response = requests.post(
        f"{BASE_AUTH_URL}/oauth/access_token",
        data={
            "client_id": settings.INSTAGRAM_APP_ID,
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    data = response.json()
    if "error_type" in data or "error" in data:
        raise InstagramAPIError(
            data.get("error_message", data.get("error", "Unknown error"))
        )
    return data  # {"access_token": ..., "user_id": ...}


def exchange_for_long_token(short_token: str) -> dict:
    """Troca o token curto pelo token longo (válido por 60 dias)."""
    response = requests.get(
        f"{BASE_GRAPH_URL}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "access_token": short_token,
        },
        timeout=30,
    )
    data = response.json()
    if "error" in data:
        raise InstagramAPIError(data["error"].get("message", "Unknown error"))
    return data  # {"access_token": ..., "token_type": ..., "expires_in": ...}


def refresh_long_token(long_token: str) -> dict:
    """Renova o token longo (executar quando expiração < 15 dias)."""
    response = requests.get(
        f"{BASE_GRAPH_URL}/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": long_token,
        },
        timeout=30,
    )
    data = response.json()
    if "error" in data:
        raise InstagramAPIError(data["error"].get("message", "Unknown error"))
    return data  # {"access_token": ..., "token_type": ..., "expires_in": ...}
