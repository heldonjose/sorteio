"""Settings para testes — herda tudo de settings.py e garante FIELD_ENCRYPTION_KEY."""
from config.settings import *  # noqa: F401, F403
from cryptography.fernet import Fernet

# Garante que a chave de criptografia existe no processo de testes
# (descartada ao fim — não persistida em lugar nenhum)
if not FIELD_ENCRYPTION_KEY:  # noqa: F405
    FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()  # noqa: F405

# Permite operações síncronas Django dentro do event loop do pytest-playwright
DJANGO_ALLOW_ASYNC_UNSAFE = True

# Os testes existentes verificam textos em português
LANGUAGE_CODE = "pt-br"
