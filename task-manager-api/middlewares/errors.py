"""Exceções de domínio e tratamento de erro centralizado.

Antes cada rota tinha seu próprio `try/except` — vários deles `except:` nus, que engoliam o erro
sem registrar nada (routes/task_routes.py:62, 137, 151, 204, 236 e equivalentes nos outros
arquivos). Agora as camadas lançam exceções de domínio e um handler único traduz para HTTP.
"""
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    status = 500
    mensagem_padrao = "Erro interno"

    def __init__(self, mensagem=None, detalhes=None):
        super().__init__(mensagem or self.mensagem_padrao)
        self.mensagem = mensagem or self.mensagem_padrao
        self.detalhes = detalhes


class ValidationError(AppError):
    status = 400
    mensagem_padrao = "Dados inválidos"


class UnauthorizedError(AppError):
    status = 401
    mensagem_padrao = "Credenciais inválidas"


class ForbiddenError(AppError):
    status = 403
    mensagem_padrao = "Acesso negado"


class NotFoundError(AppError):
    status = 404
    mensagem_padrao = "Recurso não encontrado"


class ConflictError(AppError):
    status = 409
    mensagem_padrao = "Conflito de dados"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _erro_de_dominio(erro):
        corpo = {"error": erro.mensagem}
        if erro.detalhes:
            corpo["details"] = erro.detalhes
        return jsonify(corpo), erro.status

    @app.errorhandler(404)
    def _rota_inexistente(_erro):
        return jsonify({"error": "Rota não encontrada"}), 404

    @app.errorhandler(405)
    def _metodo_nao_permitido(_erro):
        return jsonify({"error": "Método não permitido"}), 405

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        # O detalhe técnico vai para o log, não para o cliente.
        logger.exception("erro não tratado: %s", erro)
        return jsonify({"error": "Erro interno"}), 500
