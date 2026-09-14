# Deploy — Sorteio Pro

> Servidor: 165.22.191.46 | Padrão: /webapps/*/
> Nginx e Supervisor carregam configs automaticamente de /webapps/*/nginx.conf e /webapps/*/supervisor.conf

---

## Informações fixas do servidor

| Item | Valor |
|---|---|
| Porta Gunicorn | 9093 |
| Redis DB | 1 |
| Python | 3.12.2 (`python3.12`) |
| Projeto | `/webapps/sorteio/` |
| Logs | `/webapps/sorteio/logs/` |
| Static | `/webapps/sorteio/staticfiles/` |
| Domínio | `sorteio.repsys.com.br` |

---

## Passo 1 — Criar estrutura no servidor

```bash
mkdir -p /webapps/sorteio/logs
cd /webapps/sorteio
```

## Passo 2 — Clonar o repositório

```bash
git clone https://github.com/heldonjose/sorteio /webapps/sorteio
```

## Passo 3 — Criar o venv com Python 3.12

```bash
cd /webapps/sorteio
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Passo 4 — Criar o banco de dados PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER sorteio WITH PASSWORD 'SENHA_AQUI';"
sudo -u postgres psql -c "CREATE DATABASE sorteio OWNER sorteio;"
```

> Se o servidor usar a porta 5432 padrão, o comando acima funciona.
> Se precisar especificar: adicione `-p 5432` no comando.

## Passo 5 — Criar o .env

```bash
cp /webapps/sorteio/.env.exemplo /webapps/sorteio/.env
nano /webapps/sorteio/.env
```

Preencher obrigatoriamente:

```ini
APP_NAME=Sorteio Pro
SECRET_KEY=<gere com: python -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=sorteio.repsys.com.br
CSRF_TRUSTED_ORIGINS=https://sorteio.repsys.com.br
SITE_URL=https://sorteio.repsys.com.br

DATABASE_URL=postgres://sorteio:SENHA_AQUI@localhost:5432/sorteio

CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_TASK_DEFAULT_QUEUE=sorteio

INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=https://sorteio.repsys.com.br/auth/instagram/callback/

FIELD_ENCRYPTION_KEY=<gere com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

ADMIN_URL=painel-admin-troque-isto/
WHATSAPP_NUMBER=5583996279632
CONTACT_EMAIL=alinnequele@gmail.com
```

## Passo 6 — Migrar banco e compilar assets

```bash
cd /webapps/sorteio
source venv/bin/activate
python manage.py migrate
python manage.py tailwind build
python manage.py collectstatic --noinput
python manage.py setup_periodic_tasks
python manage.py createsuperuser
```

## Passo 7 — Configurar Nginx

```bash
cp /webapps/sorteio/config/server/nginx.conf /webapps/sorteio/nginx.conf
nginx -t && systemctl reload nginx
```

> O Nginx já inclui /webapps/*/nginx.conf automaticamente — não precisa criar symlink.

## Passo 8 — Certificado SSL (certbot)

```bash
certbot --nginx -d sorteio.repsys.com.br
```

> O certbot vai editar o /webapps/sorteio/nginx.conf automaticamente com os paths do certificado.
> Após isso: `nginx -t && systemctl reload nginx`

## Passo 9 — Configurar Supervisor

```bash
cp /webapps/sorteio/config/server/supervisor.conf /webapps/sorteio/supervisor.conf
supervisorctl reread
supervisorctl update
supervisorctl start sorteio_web sorteio_worker sorteio_beat
supervisorctl status
```

## Passo 10 — Verificar

```bash
# Serviços rodando?
supervisorctl status

# Site respondendo?
curl -I https://sorteio.repsys.com.br

# Logs de erro
tail -f /webapps/sorteio/logs/gunicorn_error.log
```

---

## Deploy dia a dia (atualização)

```bash
cd /webapps/sorteio
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py tailwind build
python manage.py collectstatic --noinput
supervisorctl restart sorteio_web sorteio_worker sorteio_beat
```

Ou via Fabric (da sua máquina local):
```bash
fab deploy
```

---

## Comandos úteis

```bash
# Logs em tempo real
tail -f /webapps/sorteio/logs/gunicorn_error.log
tail -f /webapps/sorteio/logs/celery_worker.log

# Reiniciar só o web (sem derrubar worker)
supervisorctl restart sorteio_web

# Django shell no servidor
cd /webapps/sorteio && source venv/bin/activate && python manage.py shell

# Backup do banco
sudo -u postgres pg_dump sorteio | gzip > /root/backup_sorteio_$(date +%Y%m%d).sql.gz
```
