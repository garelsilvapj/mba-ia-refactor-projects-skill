"""Schemas de entrada de usuário."""
from marshmallow import fields, validate

from config import Config
from schemas.base import BaseSchema

_EMAIL = validate.Regexp(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", error="Email inválido")
_SENHA = validate.Length(
    min=Config.SENHA_MIN, error=f"Senha deve ter no mínimo {Config.SENHA_MIN} caracteres"
)
_ROLE = validate.OneOf(Config.ROLES_VALIDOS, error="Role inválido")


class UserCreateSchema(BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, error="Nome é obrigatório"),
                      error_messages={"required": "Nome é obrigatório"})
    email = fields.Str(required=True, validate=_EMAIL,
                       error_messages={"required": "Email é obrigatório"})
    password = fields.Str(required=True, validate=_SENHA,
                          error_messages={"required": "Senha é obrigatória"})
    role = fields.Str(load_default=Config.ROLE_PADRAO, validate=_ROLE)


class UserUpdateSchema(BaseSchema):
    name = fields.Str(validate=validate.Length(min=1, error="Nome é obrigatório"))
    email = fields.Str(validate=_EMAIL)
    password = fields.Str(validate=validate.Length(min=Config.SENHA_MIN, error="Senha muito curta"))
    role = fields.Str(validate=_ROLE)
    active = fields.Bool()


class LoginSchema(BaseSchema):
    email = fields.Str(required=True, error_messages={"required": "Email e senha são obrigatórios"})
    password = fields.Str(required=True, error_messages={"required": "Email e senha são obrigatórios"})
