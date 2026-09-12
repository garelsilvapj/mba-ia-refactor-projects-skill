"""Schemas de entrada de tarefa."""
from marshmallow import fields, validate

from config import Config
from schemas.base import BaseSchema

_TITULO = validate.Length(
    min=Config.TITULO_MIN,
    max=Config.TITULO_MAX,
    error=f"Título deve ter entre {Config.TITULO_MIN} e {Config.TITULO_MAX} caracteres",
)
_STATUS = validate.OneOf(Config.STATUSES_VALIDOS, error="Status inválido")
_PRIORIDADE = validate.Range(
    min=Config.PRIORIDADE_MIN,
    max=Config.PRIORIDADE_MAX,
    error=f"Prioridade deve ser entre {Config.PRIORIDADE_MIN} e {Config.PRIORIDADE_MAX}",
)


class TaskCreateSchema(BaseSchema):
    title = fields.Str(required=True, validate=_TITULO, error_messages={"required": "Título é obrigatório"})
    description = fields.Str(load_default="", allow_none=True)
    status = fields.Str(load_default=Config.STATUS_PADRAO, validate=_STATUS)
    priority = fields.Int(
        load_default=Config.PRIORIDADE_PADRAO,
        validate=_PRIORIDADE,
        error_messages={"invalid": "Prioridade deve ser um número entre 1 e 5"},
    )
    user_id = fields.Int(load_default=None, allow_none=True)
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Date(
        load_default=None,
        allow_none=True,
        format="%Y-%m-%d",
        error_messages={"invalid": "Formato de data inválido. Use YYYY-MM-DD"},
    )
    tags = fields.Raw(load_default=None, allow_none=True)


class TaskUpdateSchema(BaseSchema):
    title = fields.Str(validate=_TITULO)
    description = fields.Str(allow_none=True)
    status = fields.Str(validate=_STATUS)
    priority = fields.Int(
        validate=_PRIORIDADE,
        error_messages={"invalid": "Prioridade deve ser um número entre 1 e 5"},
    )
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    due_date = fields.Date(
        allow_none=True, format="%Y-%m-%d", error_messages={"invalid": "Formato de data inválido"}
    )
    tags = fields.Raw(allow_none=True)


class TaskSearchSchema(BaseSchema):
    """Antes os parâmetros de busca iam direto para `int()`, o que devolvia 500."""

    q = fields.Str(load_default="")
    status = fields.Str(load_default=None, allow_none=True, validate=_STATUS)
    priority = fields.Int(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Prioridade deve ser um número"},
    )
    user_id = fields.Int(
        load_default=None, allow_none=True, error_messages={"invalid": "user_id deve ser um número"}
    )
    limit = fields.Int(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, max=Config.PAGINA_TAMANHO_MAX),
    )
    offset = fields.Int(load_default=0, validate=validate.Range(min=0))
