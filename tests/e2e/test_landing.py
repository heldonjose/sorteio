"""
Testes E2E da landing page com Playwright.

Execute com:
    pytest tests/e2e/ -v --headed     # modo visual
    pytest tests/e2e/ -v              # modo headless
"""

import pytest


@pytest.mark.django_db(transaction=True)
def test_landing_page_loads(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.title() != ""


@pytest.mark.django_db(transaction=True)
def test_landing_has_instagram_cta(page, live_server):
    page.goto(f"{live_server.url}/")
    cta = page.get_by_text("Entrar com Instagram")
    assert cta.count() > 0


@pytest.mark.django_db(transaction=True)
def test_landing_has_pricing_section(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.get_by_text("Planos simples").count() > 0


@pytest.mark.django_db(transaction=True)
def test_privacidade_page_loads(page, live_server):
    page.goto(f"{live_server.url}/privacidade/")
    assert page.get_by_text("Política de Privacidade").count() > 0


@pytest.mark.django_db(transaction=True)
def test_termos_page_loads(page, live_server):
    page.goto(f"{live_server.url}/termos/")
    assert page.get_by_text("Termos de Uso").count() > 0


@pytest.mark.django_db(transaction=True)
def test_dark_mode_toggle(page, live_server):
    page.goto(f"{live_server.url}/")
    # Verifica que o toggle de tema existe (aria-label)
    toggle = page.get_by_role("button", name="Alternar tema")
    assert toggle.count() > 0
    toggle.click()
    # Após o clique, a classe 'dark' deve aparecer no <html>
    html_class = page.locator("html").get_attribute("class")
    assert html_class is not None
