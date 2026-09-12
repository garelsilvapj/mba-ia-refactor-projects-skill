"""Exceções de domínio e handler de erro centralizado.

Antes: o bloco `except Exception as e: return jsonify({"erro": str(e)}), 500` aparecia 16 vezes
em controllers.py e uma em app.py, devolvendo a mensagem crua do SQLite ao cliente.

Agora: as camadas lançam exceções de domínio; um único handler traduz para HTTP, registra o
detalhe em log e devolve mensagem genérica para falhas inesperadas.
"""
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base das exceções de domínio. Cada subclasse carrega o status HTTP correspondente."""

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
    mensagem_padrao = "Não autorizado"


class NotFoundError(AppError):
    status = 404
    mensagem_padrao = "Recurso não encontrado"


class ConflictError(AppError):
    status = 409
    mensagem_padrao = "Conflito de dados"


def _corpo(mensagem, detalhes=None):
    """Envelope único de erro: mesma forma em todas as rotas."""
    corpo = {"erro": mensagem, "sucesso": False}
    if detalhes:
        corpo["detalhes"] = detalhes
    return corpo


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _erro_de_dominio(erro):
        return jsonify(_corpo(erro.mensagem, erro.detalhes)), erro.status

    @app.errorhandler(404)
    def _rota_inexistente(_erro):
        return jsonify(_corpo("Rota não encontrada")), 404

    @app.errorhandler(405)
    def _metodo_nao_permitido(_erro):
        return jsonify(_corpo("Método não permitido")), 405

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        # O detalhe técnico vai para o log; o cliente recebe uma mensagem genérica.
        logger.exception("erro não tratado: %s", erro)
        return jsonify(_corpo("Erro interno")), 500
