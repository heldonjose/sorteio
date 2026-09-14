# Subir o Sorteio no servidor

> Adaptado de `~/PROJETOS/UAST/Docencia/2026_2/docs/servidor/deploy.md` (caso do Kanban). O servidor é
> o **mesmo**: Ubuntu com **Nginx 1.24, Supervisor, PostgreSQL e certbot já instalados**, vários
> projetos em `/webapps/*`. Nada aqui instala pacote de sistema.
>
> Diferenças deste projeto para o Kanban:
> 1. **Três processos no Supervisor**, no mesmo desenho do Helios: o gunicorn (`sorteio`), o worker
>    do Celery (`sorteio-celery`), que carrega os comentários, e o beat (`sorteio-beat`), que dispara
>    as tarefas periódicas (renovar tokens, limpar comentários antigos).
>    **Requer Redis no servidor** (`redis-cli ping` → `PONG`), com um **DB só deste projeto** (§2.1).
> 2. **Tailwind** precisa ser compilado (`manage.py tailwind build`) antes do `collectstatic`.
> 3. A **Meta exige HTTPS** nas URLs do OAuth. Sem certificado não há login com Instagram.

---

## 1. A ficha do projeto

| Variável | O que é | Valor |
|---|---|---|
| `PROJETO` | nome curto; vira pasta, banco e `[program:]` | `sorteio` |
| `DOMINIO` | domínio já apontado para o IP do servidor | `sorteio.repsys.com.br` |
| `PORTA` | porta do gunicorn, livre e exclusiva | `9093` *(Controle Interno 9091, Kanban 9092; confirmar com `ss -ltnp \| grep 909`)* |
| `WSGI` | módulo WSGI | `config.wsgi` |
| `RAIZ` | virtualenv e código | `/webapps/sorteio` e `/webapps/sorteio/sorteio` |

A porta aparece em dois lugares que têm de bater: `config/server/gunicorn.conf.py` e o `upstream` do
`config/server/nginx.conf`.

---

## 2. Arquivos que o repositório vai ter (gerados na Fase 5)

```
config/server/nginx.conf          -> link em /webapps/sorteio/nginx.conf
config/server/supervisor.conf     -> link em /webapps/sorteio/supervisor.conf  (3 programas)
config/server/gunicorn.conf.py    -> lido pelo -c do supervisor
config/server/README.md
deploy.sh                          primeira subida (idempotente)
fabfile.py                         dia a dia, da sua máquina (Fabric 3)
.env.exemplo                       modelo do .env
```

Regras que valem aqui como no Kanban:

- **Nenhum segredo no Git.** `SECRET_KEY`, senha do banco, `INSTAGRAM_APP_SECRET` e `FIELD_ENCRYPTION_KEY` moram só no `.env` do servidor.
- **Configuração é link simbólico para o repositório, nunca cópia.** Nada no servidor edita esses arquivos.
- **Certificado com `certbot certonly`, jamais `certbot --nginx`.**
- **Nada de dado de demonstração em produção.**

### `supervisor.conf` (referência)

```ini
; Supervisor do Sorteio. Instalação e o que trocar: README.md desta pasta.

[program:sorteio]
command=/webapps/sorteio/bin/gunicorn -c config/server/gunicorn.conf.py config.wsgi
directory=/webapps/sorteio/sorteio
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sorteio.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5

; Worker do Celery: carrega os comentários dos sorteios.
; -Q sorteio  só consome a fila deste projeto
; -n sorteio@%h  nome de nó único no servidor (ver §2.1)
[program:sorteio-celery]
command=/webapps/sorteio/bin/celery -A config worker -l info --concurrency=2 -Q sorteio -n sorteio@%%h
directory=/webapps/sorteio/sorteio
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sorteio-celery.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
stopwaitsecs=600
killasgroup=true
priority=998

; Beat: dispara as PeriodicTask cadastradas no Admin (django-celery-beat).
; UM beat por projeto, nunca dois do mesmo projeto (duplicaria as tarefas).
[program:sorteio-beat]
command=/webapps/sorteio/bin/celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/webapps/sorteio/sorteio
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sorteio-beat.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
stopwaitsecs=600
killasgroup=true
priority=999
```

> No Supervisor, `%` precisa ser escrito `%%`. Por isso é `-n sorteio@%%h`, que vira `sorteio@<hostname>`.

### 2.1 Vários projetos com Celery no mesmo servidor

Dois projetos **podem se atrapalhar** se dividirem o mesmo Redis sem separação:

| Risco | Por quê | Proteção neste projeto |
|---|---|---|
| Worker de um projeto pegar tarefa do outro | Todos usam por padrão a fila `celery` no **DB 0** do Redis. O worker errado recebe a tarefa, loga `Received unregistered task` e a tarefa se perde | **DB próprio** (`redis://localhost:6379/1`) **e** fila própria (`CELERY_TASK_DEFAULT_QUEUE=sorteio`, `-Q sorteio`) |
| Beat de um projeto "disparar" no outro | O beat só publica mensagens na fila; se a fila é compartilhada, cai no worker errado | Mesma proteção acima. As agendas ficam no **PostgreSQL de cada projeto** (DatabaseScheduler), então não se misturam |
| Aviso `DuplicateNodenameWarning` / `celery inspect` misturado | Os dois workers se chamam `celery@<hostname>` no mesmo broker | `-n sorteio@%h` |
| Resultados misturados | Backend de resultados no mesmo Redis | Resultados no **PostgreSQL** via django-celery-results (`CELERY_RESULT_BACKEND=django-db`) |
| Cache do Django sobrescrevendo chaves | `CACHES` no mesmo DB do Redis | Se usar cache Redis, outro DB (`/2`) ou `KEY_PREFIX='sorteio'` |

Antes de escolher o número do DB, veja quais já estão em uso:

```bash
redis-cli INFO keyspace      # ex.: "db0:keys=12,..." → o Helios (se estiver neste servidor) está no 0
```

O Redis vem com 16 DBs (0–15). Este projeto usa o **1**, ou o próximo livre.

### `gunicorn.conf.py`
Igual ao do Kanban (gevent, `workers = 2`, `preload_app = False`), trocando só `bind = '127.0.0.1:9093'`.
Aqui o gevent faz ainda mais sentido: listar posts é esperar a API do Instagram.

### `nginx.conf`
Igual ao do Kanban, trocando `upstream gunicorn_sorteio` → `127.0.0.1:9093`, `server_name` → `sorteio.repsys.com.br`,
caminhos → `/webapps/sorteio/sorteio/staticfiles/` e `client_max_body_size 10m` (não há upload grande).

---

## 3. O roteiro

A ordem importa: o certificado só sai com o domínio respondendo por HTTP, e o HTTP só responde com o
gunicorn de pé. Os passos **1, 3 e 9 são seus**; os demais o `deploy.sh` faz.

### 1. DNS (você)
Registro **A** de `sorteio.repsys.com.br` para o IP do servidor. Conferir com `dig +short sorteio.repsys.com.br`.

### 2. Código e virtualenv
```bash
git clone <repo> /webapps/sorteio/sorteio
python3 -m venv /webapps/sorteio
/webapps/sorteio/bin/pip install -r /webapps/sorteio/sorteio/requirements.txt
```

### 3. O `.env` (você, à mão)
```bash
cd /webapps/sorteio/sorteio
cp .env.exemplo .env && chmod 600 .env
```

Preencher:

```ini
DATABASE_URL=postgres://postgres:<senha>@localhost:5432/sorteio
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_TASK_DEFAULT_QUEUE=sorteio
SECRET_KEY=<gerar>
DEBUG=False
ALLOWED_HOSTS=sorteio.repsys.com.br
CSRF_TRUSTED_ORIGINS=https://sorteio.repsys.com.br
SITE_URL=https://sorteio.repsys.com.br
ADMIN_URL=<caminho-nao-obvio>/

INSTAGRAM_APP_ID=<ID do app do Instagram>
INSTAGRAM_APP_SECRET=<Chave secreta do app do Instagram — REDEFINIDA>
INSTAGRAM_REDIRECT_URI=https://sorteio.repsys.com.br/auth/instagram/callback/
FIELD_ENCRYPTION_KEY=<gerar>
WHATSAPP_NUMBER=5583996279632
CONTACT_EMAIL=alinnequele@gmail.com
```

Gerar as chaves:

```bash
# SECRET_KEY
/webapps/sorteio/bin/python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
# FIELD_ENCRYPTION_KEY (cifra os tokens do Instagram no banco)
/webapps/sorteio/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ **Guarde a `FIELD_ENCRYPTION_KEY` no gerenciador de senhas.** Perdida, os tokens salvos ficam
> ilegíveis e todo mundo precisa entrar com o Instagram de novo.

### 4. Banco
```bash
sudo -u postgres createdb sorteio
psql "$DATABASE_URL" -c '\conninfo'
redis-cli -n 1 ping                      # PONG; e `redis-cli INFO keyspace` para ver os DBs já usados
```

### 5. Check, migrar, Tailwind e estáticos
```bash
manage.py check --deploy
manage.py migrate
manage.py tailwind build
manage.py collectstatic --noinput
```

### 6. Serviços
```bash
ln -sfn /webapps/sorteio/sorteio/config/server/supervisor.conf /webapps/sorteio/supervisor.conf
supervisorctl reread && supervisorctl update
supervisorctl status sorteio sorteio-celery sorteio-beat   # os três RUNNING

ln -sfn /webapps/sorteio/sorteio/config/server/nginx.conf /webapps/sorteio/nginx.conf
nginx -t && systemctl reload nginx
curl -sI http://sorteio.repsys.com.br/                      # 301
```

### 7. Certificado
```bash
mkdir -p /var/www/certbot
systemctl stop nginx
certbot certonly --standalone -d sorteio.repsys.com.br -n --agree-tos
systemctl start nginx
```

`listen 443 ssl http2;` (Nginx 1.24). O `SECURE_PROXY_SSL_HEADER` já estará no `settings.py`.

### 8. Renovação por webroot (não pular)
```bash
sed -i 's|^authenticator = standalone|authenticator = webroot\nwebroot_path = /var/www/certbot|' \
  /etc/letsencrypt/renewal/sorteio.repsys.com.br.conf
printf '\n[[webroot_map]]\nsorteio.repsys.com.br = /var/www/certbot\n' >> /etc/letsencrypt/renewal/sorteio.repsys.com.br.conf
certbot renew --dry-run      # tem que terminar em "all simulated renewals succeeded"
```

### 9. Administrador (você)
```bash
venv/bin/fab criar-admin
```

O Django Admin fica em `https://sorteio.repsys.com.br/<ADMIN_URL>`.

---

## 4. Pontos de conferência (o `deploy.sh` aborta se algum falhar)

| Comando | Prova que |
|---|---|
| `psql "$DATABASE_URL" -c '\conninfo'` | o banco existe e aceita a senha |
| `manage.py check --deploy` | o Django sobe com essa configuração de produção |
| `redis-cli -n 1 ping` | o broker do Celery responde |
| `supervisorctl status sorteio sorteio-celery sorteio-beat` | gunicorn, worker e beat de pé |
| `celery -A config inspect ping -d sorteio@$(hostname)` | o worker **deste** projeto responde pelo broker |
| `nginx -t` + `curl -sI https://sorteio.repsys.com.br/` | o Nginx leu o bloco e o site responde |
| `certbot renew --dry-run` | o certificado vai se renovar sozinho |
| `curl -s https://sorteio.repsys.com.br/privacidade/ -o /dev/null -w '%{http_code}'` → `200` | as páginas que a Meta exige estão no ar |

---

## 5. Dia a dia — `fabfile.py`

Mesmo desenho do Kanban (`SERVIDOR` igual, `PROGRAMA = 'sorteio'`, `CODIGO = '/webapps/sorteio/sorteio'`), com estas diferenças:

- `fab deploy`: `git pull` → pip → migrate → **`tailwind build`** → collectstatic → `supervisorctl restart sorteio sorteio-celery sorteio-beat`. **O worker precisa reiniciar em todo deploy**, senão continua rodando o código antigo das tarefas.
- `fab log --de=web|celery|beat` para escolher o log (`/var/log/supervisor/sorteio-*.log`).
- `fab reiniciar` reinicia os três processos (todos leem o `.env` só na subida).
- `fab celery`: `celery -A config inspect active -d sorteio@<host>` para ver as tarefas em execução.
- `fab credito --usuario=@fulano --qtd=30 --obs="Pix 13/09"`: atalho para o comando de gestão que lança créditos. O caminho normal continua sendo o Admin.

```bash
venv/bin/fab help
venv/bin/fab deploy
venv/bin/fab status
venv/bin/fab log --de=celery --seguir
```

---

## 6. Backup do banco

Backup diário no próprio servidor, com 14 dias de retenção (`crontab -e` como root):

```cron
0 3 * * * pg_dump "postgres://postgres:<senha>@localhost:5432/sorteio" | gzip > /root/backups/sorteio-$(date +\%F).sql.gz && find /root/backups -name 'sorteio-*.sql.gz' -mtime +14 -delete
```

Recomendado copiar para fora do servidor (rclone → Backblaze B2 / Google Drive) e **testar uma restauração**. Aqui há dinheiro envolvido (créditos).

---

## 7. Configurar a Meta para produção

Com o site no ar em HTTPS:

1. **Configurações do app → Básico**
   - Domínios do app: `sorteio.repsys.com.br`
   - Política de Privacidade: `https://sorteio.repsys.com.br/privacidade/`
   - Termos de Serviço: `https://sorteio.repsys.com.br/termos/`
   - Exclusão de dados: `https://sorteio.repsys.com.br/exclusao-de-dados/`
   - Ícone 1024×1024, categoria, e-mail de contato
2. **Instagram → Configuração da API com login do Instagram → 3. Configure o login da empresa**
   - URI de redirecionamento OAuth: `https://sorteio.repsys.com.br/auth/instagram/callback/`
   - Callback de desautorização: `https://sorteio.repsys.com.br/meta/deauthorize/`
   - Solicitação de exclusão de dados: `https://sorteio.repsys.com.br/meta/data-deletion/`
3. **Redefinir a chave secreta** (a atual apareceu em print), colocar a nova no `.env` e rodar `fab reiniciar`.
4. Seguir `docs/meta/APP_REVIEW.md`.

---

## 8. Desenvolvimento local com login real

A Meta não aceita `http://localhost` como redirect. Use um túnel HTTPS:

```bash
cloudflared tunnel --url http://localhost:8000     # ou: ngrok http 8000
```

Cadastre `https://<tunel>/auth/instagram/callback/` como URI extra na Meta e no `.env` local, e rode em três terminais: `manage.py runserver`, `celery -A config worker -l info -Q sorteio` e `celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`. Redis local: `sudo apt install redis-server`. Em modo desenvolvimento, só aparecem comentários de contas **Testador do Instagram**.

---

## 9. Sintomas e causas

| O que aparece | O que é |
|---|---|
| `supervisorctl status` vazio | link fora do curinga `/webapps/*/supervisor.conf` |
| Comentários ficam "carregando" para sempre | `sorteio-celery` parado, ou ouvindo outra fila: `fab status`, `fab log --de=celery` |
| `Received unregistered task` no log de um worker | dois projetos dividindo DB/fila do Redis (§2.1) |
| Tarefa periódica não roda | `sorteio-beat` parado, ou `PeriodicTask` desativada no Admin |
| Tarefa periódica roda duas vezes | dois beats do mesmo projeto de pé |
| Mudança em tarefa não surtiu efeito | worker não foi reiniciado no deploy |
| `502` | gunicorn caiu ou a porta não bate com o `upstream` |
| `Bad Request (400)` | `ALLOWED_HOSTS` sem o domínio |
| página sem estilo | faltou `tailwind build` ou `collectstatic` |
| Login do Instagram: "URL blocked" / "redirect_uri" | `INSTAGRAM_REDIRECT_URI` diferente da URI cadastrada na Meta (barra final conta) |
| Login volta com erro de `state` | cookie de sessão perdido: `CSRF_TRUSTED_ORIGINS` / HTTPS / `SESSION_COOKIE_SECURE` |
| Todos os tokens inválidos após deploy | `FIELD_ENCRYPTION_KEY` trocada ou ausente no `.env` |
| Post com muitos comentários volta 0 | app ainda em modo desenvolvimento (ver `docs/meta/APP_REVIEW.md`) |
| `Could not bind TCP port 80` na renovação | renovação ainda em `standalone` |
