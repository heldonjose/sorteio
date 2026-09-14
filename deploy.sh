#!/usr/bin/env bash
# deploy.sh — PRIMEIRO deploy no servidor (roda UMA VEZ como root)
# Uso: scp deploy.sh root@servidor: && ssh root@servidor bash deploy.sh
set -euo pipefail

APP=sorteio
DOMAIN=sorteio.repsys.com.br
APP_DIR=/srv/$APP
REPO=https://github.com/heldonjose/sorteio
PORT=9093
PYTHON=python3.12

echo "==> Atualizando sistema"
apt-get update -q
apt-get install -y -q git python3.12 python3.12-venv python3-pip \
  postgresql nginx supervisor certbot python3-certbot-nginx redis-tools curl

echo "==> Criando usuário $APP"
id -u $APP &>/dev/null || useradd --system --shell /bin/bash --home $APP_DIR $APP

echo "==> Criando estrutura de diretórios"
mkdir -p $APP_DIR /var/log/$APP /run/$APP /etc/gunicorn
chown -R $APP:$APP $APP_DIR /var/log/$APP /run/$APP

echo "==> Clonando repositório"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone $REPO $APP_DIR
else
  git -C $APP_DIR pull
fi
chown -R $APP:$APP $APP_DIR

echo "==> Criando venv e instalando dependências"
sudo -u $APP $PYTHON -m venv $APP_DIR/venv
sudo -u $APP $APP_DIR/venv/bin/pip install --upgrade pip -q
sudo -u $APP $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt -q

echo "==> Copiando arquivos de configuração do servidor"
cp $APP_DIR/config/server/nginx.conf /etc/nginx/sites-available/$APP
ln -sf /etc/nginx/sites-available/$APP /etc/nginx/sites-enabled/$APP
cp $APP_DIR/config/server/supervisor.conf /etc/supervisor/conf.d/$APP.conf
cp $APP_DIR/config/server/gunicorn.conf.py /etc/gunicorn/$APP.conf.py

echo "==> Verificando .env"
if [ ! -f "$APP_DIR/.env" ]; then
  echo "  ATENÇÃO: Copie o .env para $APP_DIR/.env antes de continuar"
  echo "  Exemplo: scp .env root@$DOMAIN:$APP_DIR/.env"
  exit 1
fi

echo "==> Migrações e static"
cd $APP_DIR
sudo -u $APP $APP_DIR/venv/bin/python manage.py migrate --noinput
sudo -u $APP $APP_DIR/venv/bin/python manage.py tailwind build
sudo -u $APP $APP_DIR/venv/bin/python manage.py collectstatic --noinput
sudo -u $APP $APP_DIR/venv/bin/python manage.py setup_periodic_tasks

echo "==> Iniciando serviços"
nginx -t && systemctl restart nginx
supervisorctl reread && supervisorctl update
supervisorctl start sorteio:*

echo "==> Obtendo certificado SSL (certbot)"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m alinnequele@gmail.com || \
  echo "  Aviso: certbot falhou. Configure o DNS e rode manualmente: certbot --nginx -d $DOMAIN"

echo ""
echo "✓ Deploy concluído. Acesse: https://$DOMAIN"
echo "  Logs: tail -f /var/log/$APP/gunicorn-error.log"
