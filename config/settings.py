from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost 127.0.0.1").split()
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split() if o]
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "django_tailwind_cli",
    "django_celery_beat",
    "django_celery_results",
    # Locais
    "apps.accounts",
    "apps.instagram",
    "apps.raffles",
    "apps.billing",
    "apps.pages",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.pages.middleware.DefaultLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.pages.context_processors.app_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Banco — fallback SQLite em desenvolvimento; DATABASE_URL obrigatória em produção
_db_url = os.getenv("DATABASE_URL")
if _db_url:
    DATABASES = {"default": dj_database_url.parse(_db_url, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Idioma em que os textos-fonte estão escritos. Fixo: se fosse "en", o Django usaria
# o catálogo inglês como reserva para o pt-br e o PT continuaria mostrando inglês.
LANGUAGE_CODE = "pt-br"
# Idioma padrão da interface (sem cookie de escolha). O navegador (Accept-Language)
# é ignorado de propósito: o padrão é sempre este, e o usuário troca no seletor EN/PT.
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
LANGUAGES = [
    ("en", "English"),
    ("pt-br", "Português"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URL do Django Admin (configurável por env para segurança)
ADMIN_URL = os.getenv("ADMIN_URL", "admin/")

# Auth
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/painel/"

# ── Celery ──────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "sorteio")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 min

# ── Tailwind CLI ─────────────────────────────────────────────────────────────
TAILWIND_CLI_SRC_CSS = BASE_DIR / "src" / "css" / "source.css"
TAILWIND_CLI_DIST_CSS = BASE_DIR / "static" / "css" / "tailwind.css"

# ── Instagram / Meta ─────────────────────────────────────────────────────────
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI", "")
INSTAGRAM_API_VERSION = os.getenv("INSTAGRAM_API_VERSION", "v24.0")

# ── Criptografia de tokens dos usuários (Fernet) ─────────────────────────────
# Gere com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY", "")

# ── Nome do produto ──────────────────────────────────────────────────────────
APP_NAME = os.getenv("APP_NAME", "Sorteio Pro")

# ── Regras de negócio ────────────────────────────────────────────────────────
FREE_RAFFLES_PER_ACCOUNT = int(os.getenv("FREE_RAFFLES_PER_ACCOUNT", "5"))
PRICE_SINGLE_CENTS = int(os.getenv("PRICE_SINGLE_CENTS", "1000"))
PACK_CREDITS = int(os.getenv("PACK_CREDITS", "30"))
PACK_PRICE_CENTS = int(os.getenv("PACK_PRICE_CENTS", "10000"))
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "5583996279632")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "alinnequele@gmail.com")

# ── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ── Sentry (monitoramento de erros em produção) ───────────────────────────────
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )

# ── Segurança em produção (aplicado apenas quando DEBUG=False) ────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
