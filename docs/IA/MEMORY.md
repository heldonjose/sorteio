# Memória acumulada — Projeto Sorteio Instagram

Arquivo para registrar decisões, padrões e aprendizados de sessões anteriores.
Atualizar conforme o projeto avança.

---

## Padrões de código confirmados

- Testes em `tests/<app>/test_*.py` (todos na pasta `tests/`, separados dos apps)
- Makefile para comandos: `make test`, `make run`, `make tailwind-watch`, etc.
- Cada modelo sempre registrado no admin ao ser criado
- Algoritmo puro em arquivo separado (`algorithm.py`) → testável sem ORM
- Criptografia em `encryption.py` → funções `encrypt()` / `decrypt()` com Fernet
- Commits: o usuário commita manualmente; Claude entrega só o **título**

---

## Decisões técnicas tomadas

- Stack: Django 5.2 LTS + PostgreSQL 16 + Celery + Redis DB 1 (fila `sorteio`)
- `django-tailwind-cli` (binário standalone, sem Node) para Tailwind
- `django-celery-beat` com `DatabaseScheduler` + `django-celery-results` no PostgreSQL
- Tokens dos usuários criptografados com Fernet (`cryptography`); chave em env
- Credenciais do app em variáveis de ambiente
- Configuração no padrão do Kanban: `python-dotenv` + `dj-database-url`
- Re-sorteio: gratuito, registrado (motivo + ganhadores de cada rodada)
- Créditos: sem validade
- Pagamento: WhatsApp manual, liberação pelo Django Admin
- Servidor: próprio, mesmo do Kanban e do Helios
- Porta Gunicorn proposta: `9093`; DB Redis: `1`
- SQLite como fallback quando DATABASE_URL não está definida (dev/tests)
- Testes: pytest + pytest-django + pytest-playwright

---

## Fases do projeto

### ✅ Fase 0 — Base (concluída em 2026-09-14)
- settings.py reescrito (dotenv, Celery, Tailwind, i18n pt-br)
- config/celery.py criado
- 5 apps criadas com modelos, admin, migrations e testes:
  - accounts: User, InstagramAccount (token Fernet)
  - billing: CreditTransaction (ledger), PurchaseRequest
  - raffles: Raffle, RaffleComment, Draw, Winner + algorithm.py
  - instagram: InstagramClient, OAuth helpers
  - pages: landing, privacidade, termos, exclusao_dados
- templates/base.html (Tailwind + HTMX + Alpine + dark mode)
- templates/pages/landing.html (hero, preços, como funciona)
- static/css/source.css (Tailwind v4 source)
- Makefile com comandos de dev
- .gitignore, .env.exemplo, pytest.ini, conftest.py
- docs/DESENVOLVIMENTO.md (guia de retomada entre PCs)

### ✅ Fase 2 — Núcleo de sorteios (concluída em 2026-09-14)
- Views: painel, historico, novo, carregar, regras, sortear, resultado, certificado
- Task Celery `load_comments` — paginação, progresso, retry por rate-limit
- HTMX: `_progresso.html` (polling), `_participantes_count.html`, `_posts.html`
- Templates: painel, novo, carregar, regras, sortear, resultado, certificado, histórico
- `pages:planos` adicionado
- `LOGIN_URL`, `LOGIN_REDIRECT_URL` em settings
- 21 testes de integração (test_views.py)
- 115 testes no total passando

### ✅ Fase 1 — Login com Instagram (concluída em 2026-09-14)
- OAuth: `/entrar/` → authorize → callback → token longo → login Django
- Callbacks Meta: `POST /meta/deauthorize/` e `POST /meta/data-deletion/`
- Task Celery `refresh_expiring_tokens` (renovação diária, skip <24h, limpa token inválido)
- Management command `setup_periodic_tasks` (cria PeriodicTask no banco)
- Templates: `accounts/login.html`, `accounts/error.html`
- Testes: `tests/accounts/test_views.py`, `tests/accounts/test_tasks.py`

### ✅ Fase 3 — Créditos e admin (concluída em 2026-09-14)
- billing/views.py: `planos`, `comprar` (PurchaseRequest + WhatsApp), `conta`, `excluir_conta`
- billing/urls.py: `/planos/`, `/planos/comprar/`, `/conta/`, `/conta/excluir/`
- templates: `pages/planos.html`, `accounts/conta.html`
- 22 testes de billing; 130 total passando

### ✅ Fase 4 — Interface completa (concluída em 2026-09-14)
- Landing: CTAs corrigidos → `accounts:login`; FAQ accordion (Alpine); CTA final
- `certificado.html`: Open Graph + Twitter Card com thumbnail do post
- `novo.html`: skeleton loader animado (HTMX `hx-trigger="load"`)
- `base.html`: OG/Twitter blocks, skip link, toast Django com auto-dismiss
- E2E: +5 testes (FAQ, accordion, CTA, seção final)

### ✅ Fase 5 — Legal + Produção (concluída em 2026-09-14)
- Páginas legais completas: privacidade, termos, exclusão de dados
- `config/server/`: gunicorn.conf.py (gevent, porta 9093), nginx.conf (HTTPS, HSTS), supervisor.conf
- `deploy.sh`: primeiro deploy (root, apt-get, venv, certbot)
- `fabfile.py`: Fabric 3 — deploy, restart, logs, backup, shell
- `config/settings.py`: LOGGING + Sentry (só ativo se SENTRY_DSN definido)
- `sentry-sdk[django]` no requirements.txt

### ✅ Fase 6 — Meta: técnico concluído (2026-09-14)
- Fix: `login_page` → `raffles:painel` para usuário logado
- `/exclusao-de-dados/status/<code>/` — view + URL + template (exigido pelo callback da Meta)
- 7 novos testes em `tests/pages/test_views.py`
- APP_REVIEW.md atualizado; ALERTA: trocar "Sorteio Insta" (contém "Insta") antes de submeter à Meta
- Restante: manual no dashboard da Meta (verificação empresa, vídeo, submissão)

---

## Meta App Review — Estado (ENVIADO em 15/09/2026)

**SUBMISSAO COMPLETA** — aguardando resposta da Meta (prazo: ate 20 dias).

Painel do app: https://developers.facebook.com/apps/1829415881559086/dashboard/?business_id=1185803250316568

- ✅ Verificação — empresa "A Q DA R DANTAS" (CNPJ 40.144.482/0001-78)
- ✅ Configurações do app
- ✅ Uso permitido — `instagram_business_basic` + `instagram_business_manage_comments`
- ✅ Tratamento de dados
- ✅ Instruções da análise
- Permissões em análise: `instagram_business_basic` + `instagram_business_manage_comments`

Pendências após aprovação:
- Clicar "Publicar" na página go_live do painel
- Remover tester "sandalias helokids" (manter até aprovação)

---

## Aprendizados e armadilhas

- API `GET /{media-id}/comments` em modo desenvolvimento devolve páginas vazias (sem erro) — testar com contas "Testador do Instagram"; para produção precisa de Acesso Avançado
- Seguir `paging.next` mesmo quando `data` vier vazio
- Crédito é debitado apenas na **primeira** rodada de sorteio (status passa para `DRAWN`)
- Saldo calculado via livro-razão (`Sum('amount')`) — nunca campo editável solto
- Débito usa `select_for_update` para evitar condição de corrida
- `FIELD_ENCRYPTION_KEY` gerada em `config/settings_test.py` (nova a cada run, ok)
- `pytest.ini` aponta para `config.settings_test` (não `config.settings`) — garante chave antes do Django inicializar
- E2E (pytest-playwright): `os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"` em `tests/e2e/conftest.py` — necessário porque playwright usa event loop interno que Django detecta como async
- Makefile: `PYTEST = $(PYTHON) -m pytest` — garante que o pytest do venv é usado, não o do sistema
- Tasks Celery: imports de módulos externos (ex: `refresh_long_token`) devem ficar no topo do arquivo, não dentro da função — permite `@patch("apps.accounts.tasks.X")` nos testes

---

## Estrutura de arquivos chave

| Arquivo | Responsabilidade |
|---|---|
| `apps/accounts/encryption.py` | encrypt() / decrypt() com Fernet |
| `apps/raffles/algorithm.py` | Algoritmo puro: filter_entries, compute_hash, sample_winners |
| `apps/raffles/models.py:Raffle.draw()` | Integra algorithm.py + transação atômica + débito |
| `apps/billing/admin.py:mark_as_paid` | Ação admin: libera créditos ao aprovar pedido |
| `config/settings.py` | Toda a configuração do projeto |
| `docs/DESENVOLVIMENTO.md` | Guia de retomada entre PCs |
