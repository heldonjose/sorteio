"""
Configuração dos testes E2E com Playwright.

Pré-requisitos (uma vez):
    playwright install chromium
    manage.py tailwind build   (para o CSS estar disponível)
"""

import os

import pytest

# pytest-playwright usa um event loop interno que Django detecta como contexto async.
# Essa flag permite operações síncronas do Django dentro desse event loop.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def base_url(live_server):
    """URL base do live_server para os testes Playwright."""
    return live_server.url
