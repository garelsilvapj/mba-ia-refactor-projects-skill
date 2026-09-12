"""Base dos schemas de entrada.

Usa marshmallow, que já era dependência declarada do projeto e nunca havia sido importada.
Toda entrada passa por aqui: um erro de formato vira 400 com a lista de campos, em vez do 500
que a comparação sem checagem de tipo produzia (routes/task_routes.py:113 e :261).
"""
from marshmallow import Schema, ValidationError as MarshmallowValidationError

from middlewares.errors import ValidationError


class BaseSchema(Schema):
    class Meta:
        # Campo desconhecido é ignorado, preservando o comportamento tolerante da API original.
        unknown = "exclude"

    def carregar(self, dados, mensagem_padrao="Dados inválidos"):
        if dados is None:
            raise ValidationError(mensagem_padrao)
        try:
            return self.load(dados)
        except MarshmallowValidationError as erro:
            primeiro_campo = next(iter(erro.messages))
            primeira_mensagem = erro.messages[primeiro_campo]
            if isinstance(primeira_mensagem, list):
                primeira_mensagem = primeira_mensagem[0]
            raise ValidationError(str(primeira_mensagem), detalhes=erro.messages) from None
