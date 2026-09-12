"""Rotas de usuários e login."""
from flask import Blueprint

from middlewares.auth import optional_auth, require_admin, require_auth


def criar_user_blueprint(controller):
    bp = Blueprint("users", __name__)

    # Cadastro e login são públicos; o resto exige token.
    bp.add_url_rule("/users", "create", optional_auth(controller.criar), methods=["POST"])
    bp.add_url_rule("/login", "login", controller.login, methods=["POST"])

    bp.add_url_rule("/users", "list", require_auth(controller.listar), methods=["GET"])
    bp.add_url_rule(
        "/users/<int:user_id>", "detail", require_auth(controller.detalhar), methods=["GET"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>", "update", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>", "delete", require_admin(controller.deletar), methods=["DELETE"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>/tasks",
        "tasks",
        require_auth(controller.tarefas_do_usuario),
        methods=["GET"],
    )
    return bp
