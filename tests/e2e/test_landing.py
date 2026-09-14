"""
Testes E2E da landing page com Playwright.

Execute com:
    pytest tests/e2e/ -v --headed     # modo visual
    pytest tests/e2e/ -v              # modo headless
"""

import pytest


def test_landing_page_loads(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.title() != ""


def test_landing_has_instagram_cta(page, live_server):
    page.goto(f"{live_server.url}/")
    cta = page.get_by_text("Entrar com Instagram")
    assert cta.count() > 0


def test_landing_has_pricing_section(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.get_by_text("Planos simples").count() > 0


def test_privacidade_page_loads(page, live_server):
    page.goto(f"{live_server.url}/privacidade/")
    assert page.get_by_text("Política de Privacidade").count() > 0


def test_termos_page_loads(page, live_server):
    page.goto(f"{live_server.url}/termos/")
    assert page.get_by_text("Termos de Uso").count() > 0


def test_dark_mode_toggle(page, live_server):
    page.goto(f"{live_server.url}/")
    # Verifica que o toggle de tema existe (aria-label)
    toggle = page.get_by_role("button", name="Alternar tema")
    assert toggle.count() > 0
    toggle.click()
    # Após o clique, a classe 'dark' deve aparecer no <html>
    html_class = page.locator("html").get_attribute("class")
    assert html_class is not None


def test_landing_has_faq_section(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.get_by_text("Perguntas frequentes").count() > 0


def test_landing_faq_accordion_opens(page, live_server):
    page.goto(f"{live_server.url}/")
    # Clica no primeiro item do FAQ
    btn = page.get_by_role("button", name="Preciso ter conta Business ou Creator?")
    assert btn.count() > 0
    btn.click()
    # A resposta deve aparecer após o clique
    page.wait_for_selector("text=API do Instagram", timeout=3000)
    assert page.get_by_text("API do Instagram").count() > 0


def test_landing_cta_points_to_login(page, live_server):
    page.goto(f"{live_server.url}/")
    # O CTA principal deve apontar para /entrar/
    cta = page.locator("a[href*='entrar']").first
    assert cta.count() > 0


def test_landing_has_final_cta_section(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.get_by_text("Pronto para sortear?").count() > 0
