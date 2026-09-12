"""Configuração da aplicação, lida do ambiente.

Antes (app.py:11-13) a URI do banco, a SECRET_KEY e o modo debug eram literais no código, e as
credenciais de SMTP estavam fixas em services/notification_service.py:7-10.

`python-dotenv` já era dependência declarada do projeto e não era usada; agora carrega o .env.
"""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool_env(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # Sem SECRET_KEY no ambiente, gera uma por execução: nada de segredo versionado.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    SECRET_KEY_FROM_ENV = bool(os.environ.get("SECRET_KEY"))

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _bool_env("DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))

    CORS_ORIGINS = [
        origem.strip()
        for origem in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origem.strip()
    ]

    # Validade do token de sessão, em segundos.
    TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", str(8 * 60 * 60)))

    # Exigência de token nas rotas protegidas.
    # Falso (padrão): a API responde exatamente como antes da refatoração, sem autenticação —
    # o contrato publicado é preservado. Verdadeiro: as rotas passam a exigir
    # `Authorization: Bearer <token>`, com papel de administrador nas rotas destrutivas.
    REQUIRE_AUTH = _bool_env("REQUIRE_AUTH", False)

    # Notificações por e-mail: sem credencial no ambiente, o envio fica desativado.
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # --- constantes de domínio (antes repetidas em rotas, models e utils) ---
    STATUSES_VALIDOS = ("pending", "in_progress", "done", "cancelled")
    STATUS_PADRAO = "pending"
    ROLES_VALIDOS = ("user", "admin", "manager")
    ROLE_PADRAO = "user"
    PRIORIDADE_MIN = 1
    PRIORIDADE_MAX = 5
    PRIORIDADE_PADRAO = 3
    TITULO_MIN = 3
    TITULO_MAX = 200
    SENHA_MIN = 4
    COR_PADRAO = "#000000"
    PAGINA_TAMANHO_MAX = 200


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DEBUG = False
