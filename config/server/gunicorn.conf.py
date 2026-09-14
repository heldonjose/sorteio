# config/server/gunicorn.conf.py
# Gunicorn com worker gevent (eficiente para I/O — chamadas à API do Instagram)
# Copiar para /etc/gunicorn/sorteio.conf.py no servidor

import multiprocessing

bind = "127.0.0.1:9093"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/sorteio/gunicorn-access.log"
errorlog  = "/var/log/sorteio/gunicorn-error.log"
loglevel  = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Graceful
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# Processo
pidfile = "/run/sorteio/gunicorn.pid"
user  = "sorteio"
group = "sorteio"
