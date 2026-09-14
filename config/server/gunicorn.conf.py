# config/server/gunicorn.conf.py
import multiprocessing

bind = "127.0.0.1:9093"
workers = 1
timeout = 120
keepalive = 5

accesslog = "/webapps/sorteio/logs/gunicorn_access.log"
errorlog  = "/webapps/sorteio/logs/gunicorn_error.log"
loglevel  = "info"

graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50
