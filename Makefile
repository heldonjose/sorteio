# ── Makefile — Sorteio Instagram ─────────────────────────────────────────────
# Uso: make <target>
# Requer: venv ativo (source venv/bin/activate) ou prefixar com venv/bin/

PYTHON  = python
MANAGE  = $(PYTHON) manage.py
PYTEST  = pytest
PIP     = pip

.PHONY: help install migrate run tailwind test test-unit test-integration test-e2e lint shell check

help:
	@echo ""
	@echo "  make install          Instala dependências do requirements.txt"
	@echo "  make migrate          Cria e aplica migrações"
	@echo "  make run              Sobe o servidor de desenvolvimento"
	@echo "  make tailwind         Build do CSS (Tailwind)"
	@echo "  make tailwind-watch   Watch do CSS em desenvolvimento"
	@echo "  make test             Roda todos os testes (unitários + integração)"
	@echo "  make test-unit        Apenas testes unitários (sem DB)"
	@echo "  make test-e2e         Testes E2E com Playwright (headless)"
	@echo "  make test-e2e-headed  Testes E2E com Playwright (visual)"
	@echo "  make lint             Roda o ruff"
	@echo "  make shell            Django shell"
	@echo "  make check            Django check --deploy"
	@echo "  make playwright-install  Instala os navegadores do Playwright"
	@echo ""

install:
	$(PIP) install -r requirements.txt

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

run:
	$(MANAGE) runserver

tailwind:
	$(MANAGE) tailwind build

tailwind-watch:
	$(MANAGE) tailwind watch

test:
	$(PYTEST) tests/ -v --ignore=tests/e2e

test-unit:
	$(PYTEST) tests/ -v -m "not django_db" --ignore=tests/e2e

test-integration:
	$(PYTEST) tests/ -v --ignore=tests/e2e

test-e2e:
	$(PYTEST) tests/e2e/ -v

test-e2e-headed:
	$(PYTEST) tests/e2e/ -v --headed

playwright-install:
	playwright install chromium

lint:
	ruff check .

shell:
	$(MANAGE) shell

check:
	$(MANAGE) check --deploy

# ── Celery (desenvolvimento local) ────────────────────────────────────────────
celery-worker:
	celery -A config worker -l info -Q sorteio

celery-beat:
	celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
