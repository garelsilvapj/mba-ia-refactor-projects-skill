"""Autenticação.

Antes (routes/user_routes.py:185-211) o login comparava hashes MD5 e devolvia
`'fake-jwt-token-' + id`, além do hash da senha no corpo da resposta.
"""
from sqlalchemy import select

from middlewares.auth import gerar_token
from middlewares.errors import ForbiddenError, UnauthorizedError
from models.user import User


class AuthService:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def login(self, dados):
        usuario = self.session.execute(
            select(User).where(User.email == dados["email"])
        ).scalar_one_or_none()

        if usuario is None or not usuario.check_password(dados["password"]):
            # Mesma mensagem para usuário inexistente e senha errada: não revela quem existe.
            raise UnauthorizedError("Credenciais inválidas")
        if not usuario.active:
            raise ForbiddenError("Usuário inativo")

        return {
            "message": "Login realizado com sucesso",
            "user": usuario.to_dict(),
            "token": gerar_token(usuario),
        }
