"""Autorização das rotas administrativas.

Antes (app.py:47-78) as duas rotas `/admin/*` eram públicas e destrutivas.

A proteção é **opcional por configuração**, para preservar o contrato da API:
  - sem `ADMIN_TOKEN` no ambiente, a rota responde como antes (e o boot avisa no log);
  - com `ADMIN_TOKEN` definido, passa a exigir o cabeçalho `X-Admin-Token`.
"""
import logging
from functools import wraps

from flask import current_app, request

from src.middlewares.errors import UnauthorizedError

logger = logging.getLogger(__name__)
_aviso_emitido = False


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global _aviso_emitido
        token_esperado = current_app.config.get("ADMIN_TOKEN")

        if not token_esperado:
            if not _aviso_emitido:
                logger.warning(
                    "ADMIN_TOKEN não configurado: rotas administrativas seguem abertas, "
                    "como no comportamento original. Defina ADMIN_TOKEN para exigir credencial."
                )
                _aviso_emitido = True
            return fn(*args, **kwargs)

        if request.headers.get("X-Admin-Token") != token_esperado:
            raise UnauthorizedError("Credencial de administrador inválida")
        return fn(*args, **kwargs)

    return wrapper
