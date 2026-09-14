"""
Configuração dos testes E2E com Playwright.

Pré-requisitos (uma vez):
    playwright install chromium
    manage.py tailwind build   (para o CSS estar disponível)
"""

import pytest


@pytest.fixture(scope="session")
def base_url(live_server):
    """URL base do live_server para os testes Playwright."""
    return live_server.url
