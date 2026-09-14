# ── Makefile — Sorteio Instagram ─────────────────────────────────────────────
# Uso: make <target>
# Requer: venv ativo (source venv/bin/activate)

PYTHON  = python
MANAGE  = $(PYTHON) manage.py
PYTEST  = pytest
PIP     = pip

.PHONY: help install migrate run tailwind tailwind-watch \
        test test-unit test-integration test-e2e test-e2e-headed \
        lint shell check setup-tasks playwright-install \
        celery-worker celery-beat

help:
	@echo ""
	@echo "  make install           Instala dependências do requirements.txt"
	@echo "  make migrate           makemigrations + migrate"
	@echo "  make run               Servidor de desenvolvimento"
	@echo "  make tailwind          Build do CSS (Tailwind)"
	@echo "  make tailwind-watch    Watch do CSS em desenvolvimento"
	@echo "  make setup-tasks       Cria PeriodicTasks do Celery Beat no banco"
	@echo "  make test              Testes unitários + integração (sem E2E)"
	@echo "  make test-e2e          Testes E2E com Playwright (headless)"
	@echo "  make test-e2e-headed   Testes E2E com Playwright (visual)"
	@echo "  make lint              Ruff"
	@echo "  make shell             Django shell"
	@echo "  make check             Django check --deploy"
	@echo "  make playwright-install  Instala navegadores do Playwright"
	@echo "  make celery-worker     Worker Celery local"
	@echo "  make celery-beat       Beat Celery local"
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

setup-tasks:
	$(MANAGE) setup_periodic_tasks

test:
	$(PYTEST) tests/ -v --ignore=tests/e2e

test-unit:
	$(PYTEST) tests/raffles/test_algorithm.py tests/instagram/test_client.py -v

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

# ── Celery (desenvolvimento local — rodar em terminais separados) ─────────────
celery-worker:
	celery -A config worker -l info -Q sorteio

celery-beat:
	celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
