# Memória acumulada — Projeto Sorteio Pro

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

- Nome do produto: **Sorteio Pro** (`APP_NAME`) — substituiu "Sorteio Insta" (proibido pela Meta)
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
- Porta Gunicorn: `9093` (definida em `config/server/gunicorn.conf.py`); DB Redis: `1`
- SQLite como fallback quando DATABASE_URL não está definida (dev/tests)
- Testes: pytest + pytest-django + pytest-playwright
- Retenção de comentários declarada à Meta: 90 dias

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
- Tailwind v4 source (hoje em `src/css/`)
- Makefile com comandos de dev
- .gitignore, .env.exemplo, pytest.ini, conftest.py
- docs/DESENVOLVIMENTO.md (guia de retomada entre PCs)

### ✅ Fase 1 — Login com Instagram (concluída em 2026-09-14)
- OAuth: `/entrar/` → authorize → callback → token longo → login Django
- Callbacks Meta: `POST /meta/deauthorize/` e `POST /meta/data-deletion/`
- Task Celery `refresh_expiring_tokens` (renovação diária, skip <24h, limpa token inválido)
- Management command `setup_periodic_tasks` (cria PeriodicTask no banco)
- Templates: `accounts/login.html`, `accounts/error.html`
- Testes: `tests/accounts/test_views.py`, `tests/accounts/test_tasks.py`

### ✅ Fase 2 — Núcleo de sorteios (concluída em 2026-09-14)
- Views: painel, historico, novo, carregar, regras, sortear, resultado, certificado
- Task Celery `load_comments` — paginação, progresso, retry por rate-limit
- HTMX: `_progresso.html` (polling), `_participantes_count.html`, `_posts.html`
- Templates: painel, novo, carregar, regras, sortear, resultado, certificado, histórico
- `pages:planos` adicionado
- `LOGIN_URL`, `LOGIN_REDIRECT_URL` em settings
- 21 testes de integração (test_views.py)
- 115 testes no total passando

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
- APP_REVIEW.md atualizado
- Nome do produto trocado para "Sorteio Pro" (antes era "Sorteio Insta")
- Parte manual no dashboard da Meta concluída e enviada em 15/09/2026 (ver abaixo)

### Pós-fase 6 — ajustes de teste (2026-09-14)
- `apps/raffles/management/commands/seed_comments.py` — popula comentários falsos para testar sorteios
- `static/img/logo.jpg` adicionado
- Admin de `Raffle` com `has_delete_permission → True` (**temporário**, ver Pendências)
- Fix HTMX: indicator com `display: none`, skeleton sem espaço vazio

---

## Meta App Review — Estado (REJEITADO em 23/09/2026, preparando reenvio)

**1º envio (15/09/2026) rejeitado em 23/09/2026** — as duas permissões, mesmo motivo: *"Screencast não alinhado com detalhes do caso de uso"*. O caso de uso em si foi considerado **permitido**. A Meta pediu no novo vídeo:
1. Fluxo de login completo da Meta; 2. usuário concedendo a permissão (tela de consentimento); 3. experiência completa do caso de uso; 4. **interface do app em inglês**, com legendas e explicação dos botões.

**Resposta (25/09/2026):** app agora é bilíngue (EN/PT) — ver "Internacionalização" abaixo. Próximo passo: regravar o screencast com a UI em inglês e reenviar ("Solicitar novamente").


Painel do app: https://developers.facebook.com/apps/1829415881559086/dashboard/?business_id=1185803250316568

- ✅ Verificação — empresa "A Q DA R DANTAS" (razão social abreviada de ALINE QUELE DA ROCHA DANTAS; CNPJ 40.144.482/0001-78; nome fantasia "Soluções e Sistemas")
- ✅ Configurações do app
- ✅ Uso permitido — `instagram_business_basic` + `instagram_business_manage_comments`
- ✅ Tratamento de dados
- ✅ Instruções da análise
- Permissões pedidas (rejeitadas no 1º envio, só pelo vídeo): `instagram_business_basic` + `instagram_business_manage_comments`

---

## Internacionalização (EN/PT) — 25/09/2026

- Textos-fonte em **português** nos templates (`{% translate %}` / `{% blocktranslate trimmed %}`) e no Python (`gettext`); tradução inglesa em `locale/en/LC_MESSAGES/django.po` (+ `.mo` versionado no git, o servidor não precisa de gettext)
- Idioma padrão = `DEFAULT_LANGUAGE` do `.env` (**`en` durante a análise da Meta**; voltar para `pt-br` depois de aprovado). `Accept-Language` do navegador é ignorado (`apps/pages/middleware.py`)
- Seletor EN/PT: `templates/components/lang_switcher.html` (POST em `/i18n/setlang/`, cookie de 1 ano). Páginas com barra própria incluem o seletor nela e sobrescrevem `{% block floating_lang_switcher %}` com vazio; as demais usam o seletor flutuante do `base.html`
- Texto novo: `make messages` → traduzir no `.po` → `make compilemessages` → commitar `.po` e `.mo`
- Testes rodam em `pt-br` (`config/settings_test.py`); testes do idioma em `tests/pages/test_i18n.py`
- Glossário EN: sorteio=giveaway, sortear=draw, re-sorteio=redraw, ganhador=winner, Painel=Dashboard

## Pendências

- [ ] Regravar screencast com UI em inglês e reenviar a análise (roteiro em `docs/projeto/meta/APP_REVIEW.md` §4.3)
- [ ] Após aprovação: `DEFAULT_LANGUAGE=pt-br` no `.env` do servidor
- [ ] Meta aprovar → clicar "Publicar" na página go_live do painel
- [ ] Após aprovação: remover tester "sandalias helokids" (manter até lá)
- [ ] Reverter `has_delete_permission` em `apps/raffles/admin.py` (RaffleAdmin) para `False` — liberado só para testes
- [ ] Confirmar DB Redis `1` no servidor
- [ ] Decidir: mascarar @ dos ganhadores no certificado público?

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
- Pasta de docs é `docs/projeto/` (minúsculo) — Linux diferencia maiúsculas

---

## Estrutura de arquivos chave

| Arquivo | Responsabilidade |
|---|---|
| `apps/accounts/encryption.py` | encrypt() / decrypt() com Fernet |
| `apps/raffles/algorithm.py` | Algoritmo puro: filter_entries, compute_hash, sample_winners |
| `apps/raffles/models.py:Raffle.draw()` | Integra algorithm.py + transação atômica + débito |
| `apps/raffles/management/commands/seed_comments.py` | Gera comentários falsos para teste |
| `apps/billing/admin.py:mark_as_paid` | Ação admin: libera créditos ao aprovar pedido |
| `config/settings.py` | Toda a configuração do projeto (inclui `APP_NAME`) |
| `docs/DESENVOLVIMENTO.md` | Guia de retomada entre PCs |
