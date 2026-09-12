"""Schemas de entrada de categoria."""
from marshmallow import fields, validate

from config import Config
from schemas.base import BaseSchema

_COR = validate.Regexp(r"^#[0-9a-fA-F]{6}$", error="Cor inválida. Use o formato #RRGGBB")


class CategoryCreateSchema(BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, error="Nome é obrigatório"),
                      error_messages={"required": "Nome é obrigatório"})
    description = fields.Str(load_default="", allow_none=True)
    # Antes a cor era aceita sem validação, embora `is_valid_color` existisse sem uso.
    color = fields.Str(load_default=Config.COR_PADRAO, validate=_COR)


class CategoryUpdateSchema(BaseSchema):
    name = fields.Str(validate=validate.Length(min=1, error="Nome é obrigatório"))
    description = fields.Str(allow_none=True)
    color = fields.Str(validate=_COR)
