# Memória acumulada — Projeto Sorteio Instagram

Arquivo para registrar decisões, padrões e aprendizados de sessões anteriores.
Atualizar conforme o projeto avança.

---

## Padrões de código confirmados

_(preencher conforme forem estabelecidos)_

---

## Decisões técnicas tomadas

- Stack definida: Django 5.2 LTS + PostgreSQL 16 + Celery + Redis DB 1 (fila `sorteio`)
- `django-tailwind-cli` (binário standalone, sem Node) para Tailwind
- `django-celery-beat` com `DatabaseScheduler` e `django-celery-results` no PostgreSQL
- Tokens dos usuários criptografados com Fernet (`cryptography`); chave em env
- Credenciais do app em variáveis de ambiente
- Configuração no padrão do Kanban: `python-dotenv` + `dj-database-url`
- Re-sorteio: gratuito, registrado (motivo + ganhadores de cada rodada)
- Créditos: sem validade
- Pagamento: WhatsApp manual, liberação pelo Django Admin
- Servidor: próprio, mesmo do Kanban e do Helios
- Porta Gunicorn proposta: `9093`; DB Redis: `1`

---

## Aprendizados e armadilhas

- API `GET /{media-id}/comments` em modo desenvolvimento devolve páginas vazias (sem erro) — testar com contas "Testador do Instagram"; para produção precisa de Acesso Avançado
- Seguir `paging.next` mesmo quando `data` vier vazio
- Crédito é debitado apenas na **primeira** rodada de sorteio (status passa para `DRAWN`)
- Saldo calculado via livro-razão (`Sum('amount')`) — nunca campo editável solto
- Débito usa `select_for_update` para evitar condição de corrida

---

## Sessões anteriores

### 2026-09-14

- Projeto iniciado; estrutura de pastas e documentação base definida
- Criada pasta `docs/IA/` com `CLAUDE.md` e este `MEMORY.md`
- Regras definidas: sem commit, sem pull/push, título apenas nos textos de commit
