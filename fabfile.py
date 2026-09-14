"""
fabfile.py — Deploy dia a dia com Fabric 3
Uso:
    fab deploy            # pull + migrate + collectstatic + restart
    fab restart           # reinicia gunicorn + celery sem deploy
    fab logs              # tail dos logs de erro
    fab shell             # Django shell no servidor
    fab createsuperuser   # cria superusuário no servidor
"""
from fabric import task, Connection

HOST  = "sorteio.repsys.com.br"
USER  = "sorteio"
APP   = "/srv/sorteio"
VENV  = f"{APP}/venv/bin"
PYTHON = f"{VENV}/python"
PIP    = f"{VENV}/pip"


def _conn() -> Connection:
    return Connection(host=HOST, user="root")


def _manage(c: Connection, cmd: str) -> None:
    c.run(f"cd {APP} && sudo -u {USER} {PYTHON} manage.py {cmd}", pty=True)


def _svc(c: Connection, action: str, target: str = "sorteio:*") -> None:
    c.run(f"supervisorctl {action} {target}")


@task
def deploy(c):
    """Pull do git, instala deps, migra, coleta static e reinicia."""
    conn = _conn()
    with conn:
        print("→ Pull")
        conn.run(f"git -C {APP} pull")

        print("→ Instalando dependências")
        conn.run(f"sudo -u {USER} {PIP} install -r {APP}/requirements.txt -q")

        print("→ Migrações")
        _manage(conn, "migrate --noinput")

        print("→ Tailwind build")
        _manage(conn, "tailwind build")

        print("→ Collectstatic")
        _manage(conn, "collectstatic --noinput")

        print("→ Restart")
        _svc(conn, "restart")

        print("✓ Deploy concluído")


@task
def restart(c):
    """Reinicia gunicorn e celery sem fazer deploy."""
    with _conn() as conn:
        _svc(conn, "restart")
        print("✓ Serviços reiniciados")


@task
def logs(c):
    """Exibe os logs de erro em tempo real."""
    with _conn() as conn:
        conn.run(f"tail -f /var/log/sorteio/gunicorn-error.log", pty=True)


@task
def celery_logs(c):
    """Exibe os logs do worker Celery."""
    with _conn() as conn:
        conn.run(f"tail -f /var/log/sorteio/celery-worker.log", pty=True)


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
        conn.run("supervisorctl status sorteio:*")


@task
def dbbackup(c):
    """Faz backup do banco PostgreSQL."""
    import datetime
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    with _conn() as conn:
        conn.run(
            f"sudo -u postgres pg_dump sorteio | gzip > /srv/backup/sorteio_{stamp}.sql.gz",
            warn=True,
        )
        print(f"✓ Backup: /srv/backup/sorteio_{stamp}.sql.gz")
