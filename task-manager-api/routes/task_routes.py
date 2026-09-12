"""Rotas de tarefas: apenas o mapeamento URL → controller.

Antes este arquivo tinha 299 linhas com regra de negócio, consultas ao ORM, serialização e
tratamento de erro dentro de cada handler.
"""
from flask import Blueprint

from middlewares.auth import require_admin, require_auth


def criar_task_blueprint(controller):
    bp = Blueprint("tasks", __name__)

    # /tasks/search e /tasks/stats antes de /tasks/<int:task_id> para evitar ambiguidade.
    bp.add_url_rule("/tasks/search", "search", require_auth(controller.pesquisar), methods=["GET"])
    bp.add_url_rule("/tasks/stats", "stats", require_auth(controller.estatisticas), methods=["GET"])

    bp.add_url_rule("/tasks", "list", require_auth(controller.listar), methods=["GET"])
    bp.add_url_rule("/tasks", "create", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "/tasks/<int:task_id>", "detail", require_auth(controller.detalhar), methods=["GET"]
    )
    bp.add_url_rule(
        "/tasks/<int:task_id>", "update", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/tasks/<int:task_id>", "delete", require_admin(controller.deletar), methods=["DELETE"]
    )
    return bp
