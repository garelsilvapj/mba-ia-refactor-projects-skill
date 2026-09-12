"""Configuração da aplicação.

Nenhum segredo literal: tudo vem do ambiente. As constantes de domínio que antes estavam
espalhadas pelo código (faixas de desconto, categorias, status) moram aqui, com fonte única.
"""
import os
import secrets


def _bool_env(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Configuração base, lida de variáveis de ambiente."""

    # [corrige CRITICAL] antes: SECRET_KEY = "minha-chave-super-secreta-123" em app.py:7.
    # Sem SECRET_KEY no ambiente geramos uma chave aleatória por processo: a aplicação sobe
    # para desenvolvimento, mas nenhum segredo fica versionado e as sessões não são forjáveis.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    SECRET_KEY_FROM_ENV = bool(os.environ.get("SECRET_KEY"))

    # [corrige CRITICAL] antes: db_path fixo em database.py:5.
    DB_PATH = os.environ.get("DB_PATH", "loja.db")

    # [corrige MEDIUM] antes: debug=True fixo em app.py:8 e app.py:88.
    DEBUG = _bool_env("DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))

    # [corrige MEDIUM] antes: CORS(app) liberado para qualquer origem em app.py:9.
    CORS_ORIGINS = [
        origem.strip()
        for origem in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origem.strip()
    ]

    # Credencial das rotas administrativas. Vazio: elas respondem como no comportamento
    # original. Preenchido: passam a exigir o cabeçalho X-Admin-Token.
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

    VERSAO = "1.0.0"

    # --- constantes de domínio (antes eram magic numbers espalhados) ---

    # antes: controllers.py:52
    CATEGORIAS_VALIDAS = (
        "informatica",
        "moveis",
        "vestuario",
        "geral",
        "eletronicos",
        "livros",
    )
    # antes: controllers.py:242
    STATUS_PEDIDO_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
    STATUS_PEDIDO_PADRAO = "pendente"

    # antes: controllers.py:47-50
    NOME_PRODUTO_MIN = 2
    NOME_PRODUTO_MAX = 200

    # antes: models.py:257-262
    FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

    TIPO_USUARIO_PADRAO = "cliente"
