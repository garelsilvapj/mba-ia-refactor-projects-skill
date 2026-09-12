"""Controller das rotas administrativas."""
from flask import jsonify

from src.middlewares.errors import AppError


class EndpointRetiradoError(AppError):
    """410 Gone: a rota existe, mas foi retirada de operação de forma permanente."""

    status = 410


class AdminController:
    def __init__(self, admin_service):
        self._service = admin_service

    def resetar_banco(self):
        self._service.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        # [corrige CRITICAL] antes (app.py:59-78) esta rota executava qualquer SQL recebido no
        # corpo da requisição, sem autenticação. Não há como torná-la segura: mesmo restrita a
        # SELECT, ela exporta qualquer tabela. A rota segue registrada e responde 410, para que
        # o cliente receba uma resposta explícita em vez de um 404 genérico.
        raise EndpointRetiradoError(
            "Endpoint removido por segurança: executava SQL arbitrário sem autenticação. "
            "Use os endpoints específicos da API."
        )
