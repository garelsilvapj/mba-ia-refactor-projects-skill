"""Regra de negócio de usuário e autenticação.

Antes: a senha era gravada em texto puro (models.py:127-128), devolvida nas respostas
(models.py:83 e 99) e o login era uma query concatenada vulnerável a injeção (models.py:110).
"""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.middlewares.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from src.models.usuario_model import EmailJaCadastrado, UsuarioModel

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


class UsuarioService:
    def __init__(self, usuario_model, config):
        self._usuarios = usuario_model
        self._config = config

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")

        nome = (dados.get("nome") or "").strip()
        email = (dados.get("email") or "").strip()
        senha = dados.get("senha") or ""

        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        if not EMAIL_RE.match(email):
            raise ValidationError("E-mail em formato inválido")

        try:
            # [corrige CRITICAL] a senha entra no banco como hash, nunca em texto puro.
            return self._usuarios.criar(
                nome, email, generate_password_hash(senha), self._config.TIPO_USUARIO_PADRAO
            )
        except EmailJaCadastrado:
            raise ConflictError("E-mail já cadastrado") from None

    def autenticar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")

        email = (dados.get("email") or "").strip()
        senha = dados.get("senha") or ""
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")

        linha = self._usuarios.buscar_por_email(email)
        # Verificação por hash, em tempo constante. Uma tentativa de injeção no e-mail é
        # tratada como texto literal e simplesmente não encontra usuário.
        if linha is None or not check_password_hash(linha["senha"], senha):
            raise UnauthorizedError("Email ou senha inválidos")
        return UsuarioModel.serializar_login(linha)
