"""
fabfile.py — Deploy dia a dia com Fabric 3
Uso:
    fab deploy            # pull + migrate + collectstatic + restart
    fab restart           # reinicia gunicorn + celery sem deploy
    fab logs              # tail do log de erro do gunicorn
    fab celery-logs       # tail do log do worker celery
    fab shell             # Django shell no servidor
    fab createsuperuser   # cria superusuário no servidor
    fab status            # status dos processos
    fab dbbackup          # backup do banco PostgreSQL
"""
from fabric import task, Connection

HOST   = "sorteio.repsys.com.br"
VENV   = "/webapps/sorteio/bin"
CODE   = "/webapps/sorteio/sorteio"
PYTHON = f"{VENV}/python"
PIP    = f"{VENV}/pip"
SVCS   = "sorteio_web sorteio_worker sorteio_beat"
LOGS   = "/webapps/sorteio/logs"


def _conn() -> Connection:
    return Connection(host=HOST, user="root")


def _manage(c: Connection, cmd: str) -> None:
    c.run(f"cd {CODE} && {PYTHON} manage.py {cmd}", pty=True)


def _confirm(question: str) -> bool:
    resp = input(f"{question} [Y/n] ").strip().lower()
    return resp in ("", "y", "s")


@task
def deploy(c):
    """Pull do git, instala deps, migra, coleta static e reinicia."""
    conn = _conn()
    with conn:
        print("→ Pull")
        conn.run(f"git -C {CODE} pull")

        print("→ Instalando dependências")
        conn.run(f"{PIP} install -r {CODE}/requirements.txt -q")

        if _confirm("→ Rodar migrate?"):
            _manage(conn, "migrate --noinput")

        if _confirm("→ Rodar tailwind build?"):
            _manage(conn, "tailwind build")

        if _confirm("→ Rodar collectstatic?"):
            _manage(conn, "collectstatic --noinput")

        print("→ Restart")
        conn.run(f"supervisorctl restart {SVCS}")

        print("✓ Deploy concluído")


@task
def restart(c):
    """Reinicia gunicorn e celery sem fazer deploy."""
    with _conn() as conn:
        conn.run(f"supervisorctl restart {SVCS}")
        print("✓ Serviços reiniciados")


@task
def logs(c):
    """Exibe os logs de erro do gunicorn em tempo real."""
    with _conn() as conn:
        conn.run(f"tail -f {LOGS}/gunicorn_error.log", pty=True)


@task
def celery_logs(c):
    """Exibe os logs do worker Celery."""
    with _conn() as conn:
        conn.run(f"tail -f {LOGS}/celery_worker.log", pty=True)


@task
def shell(c):
    """Django shell interativo no servidor."""
    with _conn() as conn:
        _manage(conn, "shell")


@task
def createsuperuser(c):
    """Cria superusuário no servidor."""
    with _conn() as conn:
        _manage(conn, "createsuperuser")


@task
def status(c):
    """Status dos processos Supervisor."""
    with _conn() as conn:
        conn.run(f"supervisorctl status {SVCS}")


@task
def dbbackup(c):
    """Faz backup do banco PostgreSQL."""
    import datetime
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    with _conn() as conn:
        conn.run(
            f"sudo -u postgres pg_dump sorteio | gzip > /webapps/back/sorteio_{stamp}.sql.gz",
            warn=True,
        )
        print(f"✓ Backup: /webapps/back/sorteio_{stamp}.sql.gz")
