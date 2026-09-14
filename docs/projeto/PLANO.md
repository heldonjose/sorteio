# Plano do Projeto — Plataforma de Sorteios para Instagram

> Documento vivo. Atualize conforme as decisões forem tomadas.
> Nome provisório do produto: **[NOME_DO_PRODUTO]** (ver "Decisões em aberto": a Meta **não permite** "Insta", "Instagram" ou "Gram" no nome do app/domínio).

---

## 1. Visão geral

Plataforma web em **Django + Django Templates** onde a pessoa:

1. Entra com a **conta profissional do Instagram** (Business ou Creator), via login oficial da Meta.
2. Escolhe um post, carrega **todos os comentários** e define as **regras** do sorteio.
3. Faz o sorteio com animação e recebe um **resultado auditável** (link público de certificado).
4. Consulta o **histórico** de sorteios com as configurações e os ganhadores de cada um.

Monetização:

| Item | Regra |
|---|---|
| Gratuito | **5 sorteios** por conta do Instagram (vitalício) |
| Avulso | **R$ 10** = 1 sorteio |
| Pacote | **R$ 100** = 30 sorteios |
| Pagamento | Contato e pagamento pelo **WhatsApp** |
| Liberação | Manual, pelo **Django Admin** |

A administração inteira fica no **Django Admin**, que tem login próprio de superusuário, separado do login do Instagram.

### Protótipo existente

`index.html`, na raiz, é o MVP em HTML puro: token colado manualmente, busca de posts, filtros e sorteio. A lógica de filtros e sorteio dele será portada para o Django.

### Lição aprendida no protótipo (importante)

Com o app em **modo desenvolvimento / acesso padrão**, a API `GET /{media-id}/comments` devolve **páginas vazias com paginação** (no teste: post com 725 comentários, 0 recebidos, sem erro). A Meta filtra os comentários de quem não tem função no app. Consequências:

- **Durante o desenvolvimento**, testar com comentários feitos por contas **Testador do Instagram**.
- **Para funcionar com o público**, é obrigatório obter **Acesso Avançado** de `instagram_business_basic` e `instagram_business_manage_comments` via **Análise do App** (ver `docs/meta/APP_REVIEW.md`).

---

## 2. Regras de negócio

### 2.1 Conta
- 1 login = 1 conta do Instagram (`ig_user_id` é a identidade única).
- A cota grátis é atrelada ao `ig_user_id`. Desconectar e reconectar **não** renova a cota.
- Contas pessoais não funcionam na API. A tela de login deve explicar como mudar para conta profissional.

### 2.2 Créditos
- Saldo = soma de um **livro-razão** de transações (nunca um campo solto editável). Tudo fica rastreável.
- Ao criar a conta, é lançada uma transação `FREE_GRANT` de +5.
- **Consumo:** −1 crédito quando o sorteio é **realizado pela primeira vez** (status passa para `DRAWN`).
  - Carregar comentários e ajustar regras **não** consome crédito.
  - Sem saldo, o botão "Sortear" leva para a página de planos.
- **Re-sorteio** (ex.: ganhador não cumpriu a regra): **gratuito** dentro do mesmo sorteio, mas **cada rodada fica registrada** (motivo, data, ganhadores) e aparece no certificado público.
- **Créditos comprados não expiram.**

### 2.3 Compra via WhatsApp
1. A pessoa escolhe "Avulso" ou "Pacote 30" na página **Planos**.
2. O sistema cria um `PurchaseRequest` com status `PENDING` e abre o WhatsApp (`https://wa.me/<numero>?text=...`) com a mensagem pronta:
   `Olá! Quero o Pacote 30 sorteios (R$ 100). Conta: @usuario — Pedido #123`.
3. O pagamento é combinado no WhatsApp (Pix etc.).
4. No Django Admin, o admin abre o pedido e usa a ação **"Marcar como pago e liberar créditos"**, que gera a transação de crédito automaticamente.
5. Também existe a ação avulsa **"Adicionar créditos (cortesia/ajuste)"** no usuário.

---

## 3. Arquitetura

| Camada | Escolha | Motivo |
|---|---|---|
| Linguagem | Python 3.12 | |
| Framework | Django 5.2 LTS | Suporte longo; mesma versão do Kanban |
| Configuração | `python-dotenv` + `dj-database-url` (padrão do Kanban) | `.env` fora do Git, `DATABASE_URL` obrigatória |
| Front | Django Templates + **Tailwind CSS** + **HTMX** + **Alpine.js** | Interface bonita e reativa sem SPA |
| Tailwind | `django-tailwind-cli` (binário standalone, sem Node) | Build simples em dev e prod |
| Banco | PostgreSQL 16 | |
| Tarefas assíncronas | **Celery** + **Redis** (DB exclusivo e fila `sorteio`) | Carregar milhares de comentários em segundo plano; mesmo padrão do Helios |
| Agendador | **django-celery-beat** (`PeriodicTask` no Admin, `DatabaseScheduler`) | Renovação diária de tokens, limpeza de dados |
| Resultados das tarefas | **django-celery-results** (`TaskResult` no Admin, no PostgreSQL) | Histórico e erros das tarefas |
| Arquivos estáticos | `collectstatic` servido pelo **Nginx** | Igual ao Kanban |
| Servidor | Gunicorn (gevent, 2 workers) sob **Supervisor**, atrás do **Nginx** + certbot | Servidor próprio, o mesmo do Kanban |
| Deploy | `/webapps/sorteio` + `deploy.sh` (1ª vez) + `fabfile.py` (Fabric 3, dia a dia) | Ver `docs/DEPLOY.md` |
| Segredos | Variáveis de ambiente (`.env`) | Nada sensível no código |
| Criptografia de tokens | `cryptography` (Fernet) com chave em env | Tokens dos usuários cifrados no banco |
| Monitoramento | Sentry (opcional) | |

### Sobre "tokens em variável de ambiente"
- **Credenciais do app** (`INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`) ficam **em variáveis de ambiente**.
- **Tokens de cada usuário** são gerados no login e mudam por pessoa, então **não cabem em env**. Eles ficam no banco, **criptografados** com a chave `FIELD_ENCRYPTION_KEY`, que fica em env.

---

## 4. Estrutura do projeto

```
Sorteioinsta/
├── config/                  # settings.py, urls, wsgi, celery.py
│   └── server/              # nginx.conf, supervisor.conf, gunicorn.conf.py (versionados)
├── apps/
│   ├── accounts/            # User, InstagramAccount, OAuth, callbacks da Meta
│   ├── instagram/           # cliente da API (posts, comentários, tokens)
│   ├── raffles/             # Raffle, Comment snapshot, Draw, Winner, regras
│   ├── billing/             # CreditTransaction, PurchaseRequest, saldo
│   └── pages/               # landing, planos, privacidade, termos, exclusão
├── templates/               # base.html, components/, páginas
├── static/                  # css (tailwind), js, img
├── docs/                    # este plano, deploy, documentos da Meta
├── .env.exemplo             # modelo do .env (o .env nunca vai para o Git)
├── deploy.sh                # primeira subida no servidor
├── fabfile.py               # deploy e comandos remotos (Fabric 3)
├── requirements.txt
└── manage.py
```

---

## 5. Modelos de dados

### accounts
**User** (`AbstractUser` customizado)
- `ig_user_id` (único), `username` = @ do Instagram
- `is_staff/is_superuser` somente para admins (login em `/<ADMIN_URL>/`)

**InstagramAccount** (1:1 com User)
- `ig_user_id`, `username`, `name`, `profile_picture_url`, `account_type`, `followers_count`, `media_count`
- `access_token` (**criptografado**), `token_expires_at`, `permissions` (lista)
- `connected_at`, `last_refreshed_at`, `deauthorized_at`

### billing
**CreditTransaction** (livro-razão, imutável)
- `user`, `amount` (+/−), `kind`: `FREE_GRANT | PURCHASE_SINGLE | PURCHASE_PACK | CONSUME | ADJUST | REFUND`
- `price_cents` (quando é compra), `raffle` (FK opcional), `purchase_request` (FK opcional)
- `note`, `created_by` (admin), `created_at`

**PurchaseRequest**
- `user`, `plan`: `SINGLE | PACK_30`, `credits`, `price_cents`
- `status`: `PENDING | PAID | CANCELED`, `paid_at`, `approved_by`, `note`

Saldo: `CreditTransaction.objects.filter(user=u).aggregate(Sum('amount'))`. O débito usa `select_for_update` para evitar corrida.

### raffles
**Raffle**
- `uuid` (público), `user`, `title` (opcional)
- Snapshot do post: `ig_media_id`, `permalink`, `caption`, `thumbnail_url`, `media_type`, `posted_at`, `comments_count`
- `status`: `DRAFT | LOADING | READY | DRAWN | FAILED`
- Progresso: `loaded_comments`, `load_started_at`, `load_finished_at`, `load_error`
- **Regras:** `unique_per_user`, `include_replies`, `exclude_owner`, `min_mentions`, `required_keyword`, `excluded_usernames` (lista), `winners_count`, `alternates_count` (suplentes), `comments_until` (data limite, opcional)
- `created_at`, `drawn_at`

**RaffleComment** (snapshot dos comentários no momento do carregamento)
- `raffle`, `ig_comment_id`, `username`, `text`, `commented_at`, `is_reply`, `parent_ig_id`
- Índice: (`raffle`, `username`)

**Draw** (cada rodada de sorteio)
- `raffle`, `round` (1, 2, ...), `valid_entries`, `participants_hash` (SHA-256 da lista válida ordenada), `rules_snapshot` (JSON), `random_source` ("secrets.SystemRandom"), `created_at`, `reason` (texto, no re-sorteio)

**Winner**
- `draw`, `position`, `is_alternate`, `username`, `comment_text`, `ig_comment_id`, `commented_at`

### Retenção (LGPD)
- `RaffleComment` é apagado **90 dias** após o sorteio, por tarefa agendada. Ficam `Draw`, `Winner` e o hash da lista, que bastam para o certificado.
- Quando a conta é excluída ou chega o callback de exclusão da Meta: apagar token, comentários e dados do perfil. Registros financeiros ficam anonimizados.

---

## 6. Integração com o Instagram

API: **Instagram API with Instagram Login** (Business Login). Versão em env: `INSTAGRAM_API_VERSION=v24.0`.

### 6.1 Login (OAuth)
1. Botão "Entrar com Instagram" redireciona para:
   ```
   https://www.instagram.com/oauth/authorize
     ?client_id={INSTAGRAM_APP_ID}
     &redirect_uri={INSTAGRAM_REDIRECT_URI}
     &response_type=code
     &scope=instagram_business_basic,instagram_business_manage_comments
     &state={token_csrf_da_sessao}
   ```
2. Callback `/auth/instagram/callback/`: validar `state`, remover o sufixo `#_` do `code`.
3. `POST https://api.instagram.com/oauth/access_token` (client_id, client_secret, grant_type=authorization_code, redirect_uri, code) retorna o token **curto** (1h) e o `user_id`.
4. `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=...&access_token=...` retorna o token **longo** (60 dias).
5. `GET /me?fields=user_id,username,name,profile_picture_url,account_type,media_count`. Em seguida, criar ou atualizar User + InstagramAccount, conceder os 5 grátis se for novo e fazer login na sessão Django.

### 6.2 Renovação de token
- `PeriodicTask` diária (django-celery-beat): tokens com expiração em < 15 dias (e com mais de 24h de vida) passam por `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=...`.
- Se falhar (senha trocada, acesso revogado), marcar a conta para pedir novo login.

### 6.3 Posts
- `GET /me/media?fields=id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count&limit=24`, com paginação por `paging.next` (botão "carregar mais" via HTMX).
- Busca por link: extrair o shortcode (`/p/`, `/reel/`, `/tv/`) e procurar em `permalink` nas páginas de mídia.

### 6.4 Comentários (tarefa Celery)
- `GET /{media-id}/comments?fields=id,text,username,timestamp,replies{id,text,username,timestamp}&limit=50`
- **Seguir `paging.next` mesmo quando `data` vier vazio** (visto no protótipo).
- Gravar em lotes (`bulk_create`) e atualizar `loaded_comments`. A tela consulta o progresso via HTMX a cada 1–2s.
- Tratar limite de uso: ler os headers `X-App-Usage` / `X-Business-Use-Case-Usage` e, em erro de limite (códigos 4, 17, 32, 613), esperar com backoff exponencial.
- Antes de sortear, mostrar "Comentários carregados às HH:MM — [Recarregar]".

### 6.5 Callbacks obrigatórios da Meta
| Callback | Rota | Ação |
|---|---|---|
| Desautorização | `POST /meta/deauthorize/` | Validar `signed_request` (HMAC-SHA256 com o app secret), apagar token, marcar `deauthorized_at` |
| Exclusão de dados | `POST /meta/data-deletion/` | Validar `signed_request`, agendar exclusão e responder `{"url": ".../exclusao-de-dados/status/<code>/", "confirmation_code": "<code>"}` |

---

## 7. Sorteio (algoritmo)

1. Montar a lista válida aplicando as regras, com a mesma lógica do protótipo:
   - ignora respostas (se `include_replies=False`)
   - exclui o dono do perfil, os usuários da lista de exclusão e os comentários após `comments_until`
   - exige palavra/hashtag e o mínimo de @menções distintas (sem contar a própria)
   - aplica 1 entrada por usuário, se configurado
2. Ordenar de forma determinística (`commented_at`, `ig_comment_id`) e calcular `participants_hash`.
3. Sortear com `secrets.SystemRandom().sample(...)` os ganhadores e suplentes, **sem repetir usuário**.
4. Numa transação atômica: debitar o crédito (se for a 1ª rodada), criar `Draw` + `Winner` e passar o status para `DRAWN`.
5. A animação no front é apenas visual: o resultado já vem decidido pelo servidor.

---

## 8. Telas e experiência (UI)

Direção visual: **moderna e caprichada**. Gradiente inspirado nas cores de criadores (roxo → magenta → laranja) com moderação, muito espaço em branco, cantos arredondados, sombras suaves, **modo escuro**, tipografia *Plus Jakarta Sans* / *Inter*, micro-animações (Alpine + CSS), confete no resultado (`canvas-confetti`) e **mobile-first**. Não usar logo nem marca do Instagram além do permitido pelas diretrizes de marca da Meta (ex.: "Entrar com Instagram" com o glifo oficial).

| # | Tela | Rota | Destaques |
|---|---|---|---|
| 1 | Landing | `/` | Hero, como funciona (3 passos), preços, FAQ, CTA "Entrar com Instagram" |
| 2 | Login | `/entrar/` | Explica requisito de conta profissional + botão OAuth |
| 3 | Painel | `/painel/` | Saldo de sorteios, CTA "Novo sorteio", últimos sorteios |
| 4 | Novo sorteio · post | `/sorteios/novo/` | Grade de posts + campo de link |
| 5 | Carregando | `/sorteios/<uuid>/carregar/` | Barra de progresso ao vivo |
| 6 | Regras | `/sorteios/<uuid>/regras/` | Filtros com contagem ao vivo (HTMX), lista de participantes com busca |
| 7 | Sortear | `/sorteios/<uuid>/sortear/` | Animação de roleta, confete, ganhadores + suplentes |
| 8 | Resultado | `/sorteios/<uuid>/` | Ganhadores, regras, rodadas, botão compartilhar, re-sortear |
| 9 | Certificado público | `/r/<uuid>/` | Sem login: post, data, regras, nº participantes, hash, ganhadores (@ parcialmente mascarado opcional) |
| 10 | Histórico | `/sorteios/` | Lista com filtros e busca |
| 11 | Planos | `/planos/` | Cards Grátis / Avulso / Pacote 30 → WhatsApp |
| 12 | Minha conta | `/conta/` | Dados, extrato de créditos, pedidos, desconectar, **excluir conta** |
| 13 | Legais | `/privacidade/`, `/termos/`, `/exclusao-de-dados/` | Obrigatórias para a Meta |

---

## 9. Django Admin

- URL configurável por env (`ADMIN_URL`, ex.: `painel-admin-x7k2/`).
- **User**: coluna de saldo, inline de `CreditTransaction` (somente leitura), ações **"+1 sorteio (R$ 10)"**, **"+30 sorteios (R$ 100)"** e **"Crédito cortesia/ajuste"** (pede quantidade e observação).
- **PurchaseRequest**: filtro por status; ação **"Marcar como pago e liberar créditos"**.
- **Raffle**: somente leitura, filtros por status e data, link para o certificado.
- **InstagramAccount**: status do token, expiração, ação "forçar renovação".
- Opcional depois: `django-unfold` para deixar o admin bonito.

---

## 10. Variáveis de ambiente

Modelo versionado em `.env.exemplo` (a criar na Fase 0), no mesmo padrão do Kanban:

```
# Django
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=sorteio.repsys.com.br
CSRF_TRUSTED_ORIGINS=https://sorteio.repsys.com.br
ADMIN_URL=painel-admin-troque-isto/
SITE_URL=https://sorteio.repsys.com.br

# Banco (obrigatória, sem padrão)
DATABASE_URL=postgres://postgres:SENHA@localhost:5432/sorteio

# Celery — DB do Redis e fila exclusivos deste projeto (ver docs/DEPLOY.md §2.1)
# Resultados vão para o PostgreSQL (CELERY_RESULT_BACKEND='django-db' fixo no settings)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_TASK_DEFAULT_QUEUE=sorteio

# Instagram (Meta)
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=https://sorteio.repsys.com.br/auth/instagram/callback/
INSTAGRAM_API_VERSION=v24.0

# Segurança
FIELD_ENCRYPTION_KEY=          # Fernet: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Negócio
FREE_RAFFLES_PER_ACCOUNT=5
PRICE_SINGLE_CENTS=1000
PACK_CREDITS=30
PACK_PRICE_CENTS=10000
WHATSAPP_NUMBER=5583996279632
CONTACT_EMAIL=alinnequele@gmail.com

# Opcionais
SENTRY_DSN=
EMAIL_URL=
```

---

## 11. Roadmap (fases)

### Fase 0 — Base do projeto
- [ ] Estrutura Django (`config/`, `apps/`), `settings.py` lendo `.env` (padrão do Kanban)
- [ ] PostgreSQL e Redis locais; `config/celery.py`, django-celery-beat e django-celery-results; worker e beat rodando
- [ ] Tailwind (`django-tailwind-cli`), HTMX, Alpine; `base.html` com design system (cores, botões, cards, modo escuro)
- [ ] Custom User, `.env.exemplo`, `.gitignore`, `requirements.txt`, lint (ruff), `git init`

### Fase 1 — Login com Instagram
- [ ] Cliente da API (`apps/instagram/client.py`) com tratamento de erro e rate limit
- [ ] OAuth completo + troca por token longo + criptografia
- [ ] Callbacks de desautorização e exclusão de dados (`signed_request`)
- [ ] Tarefa de renovação de token (`PeriodicTask` do django-celery-beat, criada por migração de dados)
- [ ] Dev local com HTTPS via túnel (cloudflared/ngrok) registrado na Meta

### Fase 2 — Núcleo de sorteios
- [ ] Listagem de posts + busca por link
- [ ] Tarefa de carregamento de comentários com progresso
- [ ] Tela de regras com contagem ao vivo
- [ ] Algoritmo de sorteio, `Draw`/`Winner`, re-sorteio registrado
- [ ] Resultado + certificado público + histórico
- [ ] Testes (regras, sorteio, débito de crédito)

### Fase 3 — Créditos e admin
- [ ] Livro-razão, saldo, débito atômico
- [ ] Página de planos + `PurchaseRequest` + link WhatsApp
- [ ] Ações do admin (liberar pedido, cortesia)
- [ ] Extrato na "Minha conta"

### Fase 4 — Interface caprichada
- [ ] Landing completa, animação do sorteio, confete, estados vazios, skeleton loaders
- [ ] Responsividade e acessibilidade; modo escuro
- [ ] Imagem de compartilhamento (Open Graph) do certificado

### Fase 5 — Legal + Produção
- [ ] Páginas de privacidade, termos e exclusão de dados (a partir de `docs/meta/`)
- [ ] `config/server/*`, `deploy.sh`, `fabfile.py` e subida no servidor com HTTPS (`docs/DEPLOY.md`)
- [ ] Backup diário do banco, Sentry, logs

### Fase 6 — Meta: verificação e Análise do App
- [ ] Verificação da empresa
- [ ] Configurações básicas do app (ícone, URLs, categoria)
- [ ] Pedido de Acesso Avançado com vídeo e instruções (`docs/meta/APP_REVIEW.md`)
- [ ] App em modo **Ao vivo**

### Fase 7 — Melhorias futuras (backlog)
- Várias contas do Instagram por usuário
- Pix automático (Mercado Pago/Asaas) no lugar do WhatsApp
- Vídeo/gravação do sorteio para postar nos stories
- Sorteio com múltiplos posts, filtro de "seguidores" (limitado pela API)
- Cupons e indicação

---

## 12. Decisões em aberto

1. **Nome** do produto (sem "Insta", "Instagram" ou "Gram"). Domínios livres consultados em 13/09/2026: `sortejusto.com.br`, `comentouganhou.com.br`, `tasorteado.com.br`, `sorteiofeito.com.br`.
2. **Empresa**: ✅ CNPJ **40.144.482/0001-78** (ME, empresário individual, aberta em 17/12/2020).
   - Nome empresarial: `ALINE QUELE DA ROCHA DANTAS 05455124412`. Usado **só na verificação da Meta**; contém CPF, então não vai para páginas públicas.
   - Nome fantasia: **Soluções e Sistemas**. Aparece nas páginas públicas.
   - Endereço: R. Cabo José Benício, 102, Maternidade, Patos/PB, CEP 58701-384.
   - E-mail de contato: alinnequele@gmail.com. Responsável e encarregado (DPO): Heldon José, WhatsApp (83) 99627-9632. O Instagram da empresa ainda será criado.
3. **Domínio**: ✅ **`sorteio.repsys.com.br`** por enquanto. Pode trocar por domínio próprio antes da Análise da Meta.
4. **Porta do gunicorn e DB do Redis**: propostas `9093` e DB `1`. Confirmar no servidor com `ss -ltnp | grep 909`, `redis-cli ping` e `redis-cli INFO keyspace`.
5. ✅ Decidido em 13/09/2026: hospedagem no **servidor próprio** (o mesmo do Kanban); **re-sorteio grátis e registrado**; **créditos sem validade**; **Celery + Redis + django-celery-beat + django-celery-results** (padrão do Helios).
6. **WhatsApp** de vendas: ✅ **(83) 99627-9632** (`WHATSAPP_NUMBER=5583996279632`).
7. **Retenção** dos comentários: 90 dias está ok?
8. Certificado público deve **mascarar** o @ dos ganhadores?

## 13. Aviso sobre promoções (não é consultoria jurídica)

- No Brasil, **promoções comerciais com sorteio** feitas por empresas podem exigir autorização prévia (Lei 5.768/1971; hoje com a Secretaria de Prêmios e Apostas do Ministério da Fazenda). Os Termos de Uso deixam claro que a plataforma é só uma ferramenta e que a responsabilidade legal é do organizador.
- As **Diretrizes de Promoções do Instagram** exigem que o organizador isente o Instagram e informe que a promoção não é patrocinada por ele, e proíbem incentivar marcações imprecisas. Isso também está nos Termos.
