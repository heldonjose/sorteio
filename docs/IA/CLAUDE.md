# Instruções para o Claude — Projeto Sorteio Instagram

Leia este arquivo ao iniciar qualquer sessão neste projeto. Ele contém as regras de trabalho e o contexto completo do projeto.

---

## Regras obrigatórias

1. **Nunca commitar** — não execute `git commit` em nenhuma circunstância.
2. **Nunca dar pull nem push** — não execute `git pull`, `git push` nem nenhuma operação remota do git.
3. **Texto de commit** — quando o usuário pedir uma sugestão de mensagem de commit, retorne **somente o título** (uma linha), sem corpo, sem bullet points, sem explicação adicional.

---

## Sobre o projeto

**Plataforma de sorteios para Instagram** — Django + Django Templates.

- Repositório: https://github.com/heldonjose/sorteio
- Domínio atual: `sorteio.repsys.com.br`
- Servidor: próprio (mesmo do Kanban e do Helios)

### Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | Django 5.2 LTS |
| Front | Django Templates + Tailwind CSS (`django-tailwind-cli`) + HTMX + Alpine.js |
| Banco | PostgreSQL 16 |
| Fila | Celery + Redis (DB 1, fila `sorteio`) |
| Agendador | django-celery-beat + django-celery-results |
| Servidor | Gunicorn (gevent) + Supervisor + Nginx + certbot |
| Deploy | `deploy.sh` (1ª vez) + `fabfile.py` (Fabric 3, dia a dia) |
| Config | `python-dotenv` + `dj-database-url` + `.env` fora do Git |
| Criptografia | `cryptography` (Fernet) para tokens dos usuários no banco |

### Estrutura de pastas

```
Sorteioinsta/
├── config/              # settings.py, urls, wsgi, celery.py
│   └── server/          # nginx.conf, supervisor.conf, gunicorn.conf.py
├── apps/
│   ├── accounts/        # User, InstagramAccount, OAuth, callbacks Meta
│   ├── instagram/       # cliente da API (posts, comentários, tokens)
│   ├── raffles/         # Raffle, RaffleComment, Draw, Winner, regras
│   ├── billing/         # CreditTransaction, PurchaseRequest, saldo
│   └── pages/           # landing, planos, privacidade, termos, exclusão
├── templates/           # base.html, components/, páginas
├── static/              # css (tailwind), js, img
├── docs/                # plano, deploy, docs da Meta, pasta IA/
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

- CNPJ: 40.144.482/0001-78 (ME)
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

Ver `docs/Projeto/PLANO.md` para o roadmap completo com checkboxes. O projeto está no início — estrutura base ainda sendo criada.

### Decisões abertas (consultar usuário se necessário)

- Nome do produto (sem "Insta", "Instagram" ou "Gram")
- Mascarar @ dos ganhadores no certificado público?
- Retenção de comentários: 90 dias está ok?
- Porta do Gunicorn: `9093`; DB Redis: `1` (confirmar no servidor)

---

## Arquivos de referência no projeto

| Arquivo | Conteúdo |
|---|---|
| `docs/Projeto/PLANO.md` | Plano completo: modelos, telas, roadmap, regras de negócio |
| `docs/Projeto/DEPLOY.md` | Instruções de deploy no servidor |
| `docs/Projeto/meta/APP_REVIEW.md` | Processo de Análise do App na Meta |
| `docs/Projeto/meta/POLITICA_DE_PRIVACIDADE.md` | Política de privacidade |
| `docs/Projeto/meta/TERMOS_DE_USO.md` | Termos de uso |
| `docs/Projeto/meta/EXCLUSAO_DE_DADOS.md` | Exclusão de dados (obrigatória Meta) |
| `docs/IA/MEMORY.md` | Memória acumulada de sessões anteriores (padrões, decisões, aprendizados) |

---

## Memória de sessões anteriores

Ver `docs/IA/MEMORY.md` para decisões e padrões acumulados ao longo do desenvolvimento.
