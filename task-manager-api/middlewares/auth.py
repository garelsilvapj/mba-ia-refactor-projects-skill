"""Autenticação e autorização.

Antes o login devolvia `'fake-jwt-token-' + id` (routes/user_routes.py:210), um token previsível
que nenhuma rota verificava — as 22 rotas eram públicas, inclusive as destrutivas.

Agora o token é assinado com a SECRET_KEY (itsdangerous, já disponível via Flask), tem validade e
é verificado por estes decorators.
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from middlewares.errors import ForbiddenError, UnauthorizedError


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="task-manager-auth")


def gerar_token(usuario):
    return _serializer().dumps({"user_id": usuario.id, "role": usuario.role})


def _usuario_do_token():
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        raise UnauthorizedError("Token de autenticação ausente")

    try:
        dados = _serializer().loads(
            cabecalho[len("Bearer ") :], max_age=current_app.config["TOKEN_MAX_AGE"]
        )
    except SignatureExpired:
        raise UnauthorizedError("Token expirado") from None
    except BadSignature:
        raise UnauthorizedError("Token inválido") from None

    from models.user import User  # import tardio: evita ciclo na importação dos models

    usuario = current_app.extensions["sqlalchemy"].session.get(User, dados["user_id"])
    if usuario is None or not usuario.active:
        raise UnauthorizedError("Usuário inválido ou inativo")
    return usuario


def _exigencia_ativa():
    """A exigência de token é opcional por configuração (REQUIRE_AUTH).

    Desligada (padrão), a API responde exatamente como antes da refatoração: o contrato
    publicado é preservado e nenhum endpoint deixa de responder. Ligada, as rotas protegidas
    passam a exigir token — e o token já é real e assinado nos dois modos.
    """
    return bool(current_app.config.get("REQUIRE_AUTH", False))


def require_auth(fn):
    """Exige um token válido quando REQUIRE_AUTH está ligado.

    Em ambos os modos, um token válido enviado na requisição identifica o usuário em
    `g.usuario`; o que muda é apenas se a ausência do token bloqueia ou não.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _exigencia_ativa():
            g.usuario = _usuario_do_token()
        else:
            g.usuario = _usuario_do_token_se_houver()
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    """Exige token de administrador quando REQUIRE_AUTH está ligado."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _exigencia_ativa():
            g.usuario = _usuario_do_token()
            if not g.usuario.is_admin():
                raise ForbiddenError("Ação restrita a administradores")
        else:
            g.usuario = _usuario_do_token_se_houver()
        return fn(*args, **kwargs)

    return wrapper


def _usuario_do_token_se_houver():
    """Resolve o usuário quando há token válido; devolve None em vez de bloquear."""
    if not request.headers.get("Authorization", "").startswith("Bearer "):
        return None
    try:
        return _usuario_do_token()
    except UnauthorizedError:
        return None


def optional_auth(fn):
    """Aceita a requisição sem token, mas identifica o usuário quando um token válido vem junto.

    Usado no cadastro público: qualquer pessoa se registra, mas só um administrador autenticado
    pode escolher o papel do usuário criado.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.usuario = _usuario_do_token_se_houver()
        return fn(*args, **kwargs)

    return wrapper
