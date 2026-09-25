# Instruções para o Claude — Projeto Sorteio Pro

Leia este arquivo ao iniciar qualquer sessão neste projeto. Ele contém as regras de trabalho e o contexto completo do projeto.

---

## Regras obrigatórias

1. **Nunca commitar** — não execute `git commit` em nenhuma circunstância.
2. **Nunca dar pull nem push** — não execute `git pull`, `git push` nem nenhuma operação remota do git.
3. **Texto de commit** — quando o usuário pedir uma sugestão de mensagem de commit, retorne **somente o título** (uma linha), sem corpo, sem bullet points, sem explicação adicional.

---

## Sobre o projeto

**Sorteio Pro** — plataforma de sorteios com comentários do Instagram — Django + Django Templates.

- Nome do produto: **Sorteio Pro** (`APP_NAME` no `.env`; default em `config/settings.py`). Nunca usar "Insta", "Instagram" ou "Gram" no nome (regra da Meta).
- Repositório: https://github.com/heldonjose/sorteio
- Domínio atual: `sorteio.repsys.com.br`
- Servidor: próprio (mesmo do Kanban e do Helios)

### Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | Django 5.2 LTS |
| Front | Django Templates + Tailwind CSS (`django-tailwind-cli`) + HTMX + Alpine.js |
| Banco | PostgreSQL 16 (SQLite como fallback em dev/testes) |
| Fila | Celery + Redis (DB 1, fila `sorteio`) |
| Agendador | django-celery-beat + django-celery-results |
| Servidor | Gunicorn (gevent, `127.0.0.1:9093`) + Supervisor + Nginx + certbot |
| Deploy | `deploy.sh` (1ª vez) + `fabfile.py` (Fabric 3, dia a dia) |
| Config | `python-dotenv` + `dj-database-url` + `.env` fora do Git |
| Criptografia | `cryptography` (Fernet) para tokens dos usuários no banco |
| Testes | pytest + pytest-django + pytest-playwright |
| Monitoramento | Sentry (ativo só se `SENTRY_DSN` definido) |

### Estrutura de pastas

```
sorteio/
├── config/              # settings.py, settings_test.py, urls, wsgi, celery.py
│   └── server/          # nginx.conf, supervisor.conf, gunicorn.conf.py
├── apps/
│   ├── accounts/        # User, InstagramAccount, OAuth, callbacks Meta, encryption.py
│   ├── instagram/       # cliente da API (posts, comentários, tokens)
│   ├── raffles/         # Raffle, RaffleComment, Draw, Winner, algorithm.py
│   ├── billing/         # CreditTransaction, PurchaseRequest, saldo, conta
│   └── pages/           # landing, planos, privacidade, termos, exclusão
├── templates/           # base.html, components/, páginas
├── src/css/             # fonte do Tailwind
├── static/              # css compilado, js, img
├── tests/               # tests/<app>/test_*.py + tests/e2e/
├── docs/                # DESENVOLVIMENTO.md, DEPLOY.md, projeto/, IA/
├── Makefile             # make test, make run, make tailwind-watch...
├── deploy.sh / fabfile.py
├── manage.py
└── requirements.txt
```

### Negócio

- **Gratuito:** 5 sorteios por conta do Instagram (vitalício)
- **Avulso:** R$ 10 = 1 sorteio
- **Pacote:** R$ 100 = 30 sorteios
- **Pagamento:** via WhatsApp — liberação manual pelo Django Admin
- **WhatsApp vendas:** (83) 99627-9632 (`WHATSAPP_NUMBER=5583996279632`)
- **Re-sorteio:** gratuito, registrado no mesmo sorteio
- **Créditos:** não expiram

### Empresa (para verificação Meta)

- CNPJ: 40.144.482/0001-78 (empresário individual / ME)
- Razão social: ALINE QUELE DA ROCHA DANTAS 05455124412 (aparece na Meta como "A Q DA R DANTAS")
- Nome fantasia: Soluções e Sistemas
- E-mail: alinnequele@gmail.com
- DPO/Responsável: Heldon José, WhatsApp (83) 99627-9632

### API Instagram

- **Instagram API with Instagram Login** (Business Login)
- Versão: `INSTAGRAM_API_VERSION=v24.0`
- Scopes: `instagram_business_basic`, `instagram_business_manage_comments`
- Tokens dos usuários: criptografados no banco com Fernet (`FIELD_ENCRYPTION_KEY`)
- Tokens da app: em variáveis de ambiente (`INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`)
- **Atenção:** em modo desenvolvimento, `GET /{media-id}/comments` retorna páginas vazias — testar com contas "Testador do Instagram". Para produção, é necessário Acesso Avançado via Análise do App.

### Fase atual do projeto

- Fases 0 a 6 **concluídas** (código completo, 130+ testes passando) — detalhes em `docs/IA/MEMORY.md` e `docs/DESENVOLVIMENTO.md`.
- **Análise do App na Meta rejeitada em 23/09/2026** (só o screencast; caso de uso aprovado) — app ficou bilíngue EN/PT em 25/09/2026, falta regravar o vídeo em inglês e reenviar.
- i18n: textos-fonte em português + `locale/en/`; idioma padrão pelo `DEFAULT_LANGUAGE` do `.env` (`LANGUAGE_CODE` fica fixo em `pt-br`, idioma-fonte) (ver `docs/IA/MEMORY.md` → Internacionalização).
- Pendências conhecidas: ver seção "Pendências" em `docs/IA/MEMORY.md`.

### Decisões abertas (consultar usuário se necessário)

- Mascarar @ dos ganhadores no certificado público?
- Retenção de comentários: 90 dias está ok? (é o valor declarado à Meta)
- DB Redis `1`: confirmar no servidor

---

## Arquivos de referência no projeto

| Arquivo | Conteúdo |
|---|---|
| `docs/projeto/PLANO.md` | Plano completo: modelos, telas, roadmap, regras de negócio |
| `docs/projeto/DEPLOY.md` | Instruções de deploy no servidor |
| `docs/DESENVOLVIMENTO.md` | Guia de retomada entre PCs + checklist das fases |
| `docs/projeto/meta/APP_REVIEW.md` | Processo de Análise do App na Meta |
| `docs/projeto/meta/POLITICA_DE_PRIVACIDADE.md` | Política de privacidade |
| `docs/projeto/meta/TERMOS_DE_USO.md` | Termos de uso |
| `docs/projeto/meta/EXCLUSAO_DE_DADOS.md` | Exclusão de dados (obrigatória Meta) |
| `docs/IA/MEMORY.md` | Memória acumulada de sessões anteriores (padrões, decisões, aprendizados) |

---

## Memória de sessões anteriores

Ver `docs/IA/MEMORY.md` para decisões e padrões acumulados ao longo do desenvolvimento.
