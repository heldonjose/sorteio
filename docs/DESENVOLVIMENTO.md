# Guia de desenvolvimento — Sorteio Instagram

> **Documento de retomada.** Se você está em um PC novo ou voltando depois de dias parado,
> comece aqui. Este arquivo diz exatamente onde o projeto está e o que fazer a seguir.

---

## 1. Clonar e configurar (primeira vez no PC)

```bash
git clone https://github.com/heldonjose/sorteio .
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
playwright install chromium     # para testes E2E
```

Crie o `.env` a partir do exemplo:
```bash
cp .env.exemplo .env
```

Edite `.env` e preencha pelo menos:
```ini
SECRET_KEY=qualquer-coisa-para-dev
FIELD_ENCRYPTION_KEY=<gere com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
# DATABASE_URL=  (opcional em dev — usa SQLite por padrão)
```

Suba o banco e rode:
```bash
make migrate
make tailwind       # compila o CSS (obrigatório antes de abrir no browser)
make run
```

Acesse: http://localhost:8000 | Admin: http://localhost:8000/admin/

---

## 2. Comandos do dia a dia

| Comando | O que faz |
|---|---|
| `make run` | Servidor de desenvolvimento |
| `make tailwind-watch` | CSS em modo watch (em paralelo com `make run`) |
| `make migrate` | `makemigrations` + `migrate` |
| `make test` | Todos os testes (sem E2E) |
| `make test-e2e` | Playwright headless (precisa de `make tailwind` antes) |
| `make lint` | Ruff |
| `make celery-worker` | Worker Celery local (para testar tarefas assíncronas) |
| `make celery-beat` | Beat (tarefas periódicas) |

---

## 3. Estado atual do projeto

### ✅ Fase 0 — Base (concluída em 2026-09-14)

- [x] `config/settings.py` — dotenv + dj-database-url, padrão do Kanban
- [x] `config/celery.py` — Celery configurado, fila `sorteio`, Redis DB 1
- [x] `apps/accounts/` — User (AbstractUser + ig_user_id) + InstagramAccount (token Fernet)
- [x] `apps/billing/` — CreditTransaction (livro-razão) + PurchaseRequest
- [x] `apps/raffles/` — Raffle, RaffleComment, Draw, Winner + algoritmo isolado
- [x] `apps/instagram/` — cliente da API (InstagramClient, OAuth helpers)
- [x] `apps/pages/` — landing, privacidade, termos, exclusão de dados (stubs)
- [x] Admin registrado para todos os modelos
- [x] Testes: unitários (algorithm), integração (models + draw), E2E Playwright
- [x] `templates/base.html` — Tailwind + HTMX + Alpine.js + dark mode
- [x] `templates/pages/landing.html` — hero, preços, como funciona
- [x] `static/css/source.css` — fonte + tema de cores
- [x] `Makefile` — comandos de desenvolvimento
- [x] `.gitignore`, `.env.exemplo`, `pytest.ini`

### ✅ Fix — Setup de testes (2026-09-14)

- [x] `Makefile`: `PYTEST = $(PYTHON) -m pytest` (usa o pytest do venv, não o do sistema)
- [x] `pytest.ini`: aponta para `config.settings_test` em vez de `config.settings`
- [x] `config/settings_test.py`: auto-gera `FIELD_ENCRYPTION_KEY` para testes (resolve timing do pytest-django)
- [x] `tests/e2e/conftest.py`: `DJANGO_ALLOW_ASYNC_UNSAFE=true` (compatibilidade pytest-playwright)
- [x] `apps/accounts/tasks.py`: imports de módulos externos no nível do módulo (permite `@patch`)

### ✅ Fase 1 — Login com Instagram (concluída em 2026-09-14)

- [x] OAuth completo: `/entrar/` → `/auth/instagram/authorize/` → callback → token longo
- [x] Criptografia do token ao salvar `InstagramAccount` (property Fernet)
- [x] Callback de desautorização: `POST /meta/deauthorize/`
- [x] Callback de exclusão de dados: `POST /meta/data-deletion/`
- [x] Tarefa Celery `refresh_expiring_tokens` — renovação diária de tokens
- [x] Management command `setup_periodic_tasks` — cria a PeriodicTask no banco
- [x] Testes: views (mocks da API), task (refresh + erros + skip)
- [ ] Dev local com HTTPS: `cloudflared tunnel --url http://localhost:8000` (manual)

### ✅ Fase 2 — Núcleo de sorteios (concluída em 2026-09-14)

- [x] `apps/raffles/views.py` — painel, historico, novo, carregar, regras, sortear, resultado, certificado
- [x] `apps/raffles/urls.py` — rotas completas (`/painel/`, `/sorteios/…`, `/r/<uuid>/`)
- [x] `apps/raffles/tasks.py` — `load_comments` (Celery, paginação, progresso, retry rate-limit)
- [x] Templates: painel, novo, carregar, regras, sortear, resultado, certificado, histórico
- [x] HTMX: `_progresso.html` (polling 1.5s), `_participantes_count.html`, `_posts.html`
- [x] `pages:planos` — view + template + URL
- [x] `config/settings.py` — `LOGIN_URL`, `LOGIN_REDIRECT_URL`
- [x] Callback de login → redireciona para `raffles:painel`
- [x] 21 testes de integração (115 total passando)

### 🔲 Fase 3 — Créditos e admin

- [ ] Listagem de posts + busca por link (`GET /me/media`)
- [ ] Tarefa Celery de carregamento de comentários com progresso (HTMX)
- [ ] Tela de regras com contagem ao vivo
- [ ] Algoritmo de sorteio integrado à view + animação + confete
- [ ] Resultado + certificado público (`/r/<uuid>/`)
- [ ] Histórico de sorteios

### ✅ Fase 3 — Créditos e admin (concluída em 2026-09-14)

- [x] `apps/billing/views.py` — `planos`, `comprar` (cria PurchaseRequest + abre WhatsApp), `conta`, `excluir_conta`
- [x] `apps/billing/urls.py` — `/planos/`, `/planos/comprar/`, `/conta/`, `/conta/excluir/`
- [x] `templates/pages/planos.html` — botões fazem POST para criar pedido antes do WhatsApp
- [x] `templates/accounts/conta.html` — extrato, pedidos, sair, excluir conta (confirmação Alpine)
- [x] 22 testes de billing (130 total passando)

### ✅ Fase 4 — Interface completa (concluída em 2026-09-14)

- [x] Landing: CTAs corrigidos (apontam para `accounts:login` em vez de `pages:landing`)
- [x] Landing: seção FAQ com accordion Alpine.js (5 perguntas fixas)
- [x] Landing: CTA final ("Pronto para sortear?")
- [x] `certificado.html`: Open Graph + Twitter Card com thumbnail do post
- [x] `novo.html`: skeleton loader animado (HTMX `hx-trigger="load"`) enquanto busca posts
- [x] `base.html`: Open Graph / Twitter Card completos, skip link (acessibilidade), toast Django com auto-dismiss
- [x] E2E Playwright: 5 novos testes (FAQ, accordion, CTA, seção final)

### 🔲 Fase 5 — Legal + Produção

- [ ] Páginas de privacidade, termos e exclusão de dados (a partir de `docs/projeto/meta/`)
- [ ] `config/server/` (nginx, supervisor, gunicorn), `deploy.sh`, `fabfile.py`
- [ ] Backup, Sentry, logs

### 🔲 Fase 6 — Meta: verificação e Análise do App

- [ ] Verificação da empresa (CNPJ 40.144.482/0001-78)
- [ ] Pedido de Acesso Avançado (`instagram_business_basic` e `instagram_business_manage_comments`)
- [ ] App em modo **Ao vivo**

---

## 4. Arquitetura resumida

```
config/
  settings.py    → lê .env; DATABASE_URL (SQLite se vazio); Celery; Tailwind
  celery.py      → app Celery 'sorteio', autodiscover_tasks
  urls.py        → ADMIN_URL do env + include pages

apps/
  accounts/      → User, InstagramAccount (token Fernet), encryption.py
  instagram/     → InstagramClient, OAuth helpers (client.py)
  raffles/       → Raffle, RaffleComment, Draw, Winner; algorithm.py (puro)
  billing/       → CreditTransaction (ledger), PurchaseRequest
  pages/         → landing, privacidade, termos, exclusao_dados

tests/
  accounts/      → test_models.py
  billing/       → test_models.py
  raffles/       → test_algorithm.py (sem DB), test_models.py (integração)
  instagram/     → test_client.py (mocks)
  pages/         → test_views.py
  e2e/           → test_landing.py (Playwright)

templates/
  base.html              → Tailwind, HTMX, Alpine.js, dark mode
  pages/landing.html     → hero, 3 passos, preços
  pages/privacidade.html → stub (preencher da docs/projeto/meta/)
  pages/termos.html      → stub
  pages/exclusao_dados.html → stub
```

---

## 5. Decisões importantes

| Decisão | Detalhe |
|---|---|
| Token do usuário | Criptografado com Fernet (`FIELD_ENCRYPTION_KEY`). Nunca em texto claro no banco. |
| Algoritmo de sorteio | Em `apps/raffles/algorithm.py` (funções puras, testáveis sem ORM) |
| Crédito | Livro-razão imutável (`CreditTransaction`). Saldo = `Sum('amount')`. |
| Débito | Via `select_for_update` para evitar corrida. Só na 1ª rodada de cada sorteio. |
| Re-sorteio | Gratuito. Registrado com motivo na `Draw` de rodada seguinte. |
| Celery | Redis DB 1, fila `sorteio`, resultados no PostgreSQL (`django-db`) |
| Testes | pytest + pytest-django + pytest-playwright. Todos em `tests/<app>/`. |
| Settings de teste | `config/settings_test.py` (herda `settings.py` + gera `FIELD_ENCRYPTION_KEY`). O `pytest.ini` aponta para ele. |
| E2E + Django | `DJANGO_ALLOW_ASYNC_UNSAFE=true` em `tests/e2e/conftest.py` — necessário por causa do event loop interno do pytest-playwright. |

---

## 6. Regras para o Claude (IA)

- **Nunca commitar** (`git commit`)
- **Nunca pull/push** (`git pull`, `git push`)
- Quando pedir texto de commit: retornar **só o título** (uma linha)
- Ao concluir cada fase: avisar o título do commit e anotar em `docs/IA/MEMORY.md`
- Testes: unitário + integração + Playwright desde o início de cada feature
- Todo modelo novo: registrar no admin imediatamente

---

## 7. Links rápidos

| O quê | Onde |
|---|---|
| Plano completo | `docs/projeto/PLANO.md` |
| Deploy | `docs/projeto/DEPLOY.md` |
| App Review Meta | `docs/projeto/meta/APP_REVIEW.md` |
| Memória da IA | `docs/IA/MEMORY.md` |
| Instruções para Claude | `docs/IA/CLAUDE.md` |
