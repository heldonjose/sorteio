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

### ✅ Fase 1 — Login com Instagram (concluída em 2026-09-14)
- OAuth: `/entrar/` → authorize → callback → token longo → login Django
- Callbacks Meta: `POST /meta/deauthorize/` e `POST /meta/data-deletion/`
- Task Celery `refresh_expiring_tokens` (renovação diária, skip <24h, limpa token inválido)
- Management command `setup_periodic_tasks` (cria PeriodicTask no banco)
- Templates: `accounts/login.html`, `accounts/error.html`
- Testes: `tests/accounts/test_views.py`, `tests/accounts/test_tasks.py`

### 🔲 Fases 2–6
Ver docs/DESENVOLVIMENTO.md para o roadmap completo.

---

## Aprendizados e armadilhas

- API `GET /{media-id}/comments` em modo desenvolvimento devolve páginas vazias (sem erro) — testar com contas "Testador do Instagram"; para produção precisa de Acesso Avançado
- Seguir `paging.next` mesmo quando `data` vier vazio
- Crédito é debitado apenas na **primeira** rodada de sorteio (status passa para `DRAWN`)
- Saldo calculado via livro-razão (`Sum('amount')`) — nunca campo editável solto
- Débito usa `select_for_update` para evitar condição de corrida
- `FIELD_ENCRYPTION_KEY` gerada em `conftest.py` para testes (nova a cada run, ok)

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
