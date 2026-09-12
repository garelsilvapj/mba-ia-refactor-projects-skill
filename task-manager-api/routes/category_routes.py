"""Rotas de categorias.

Antes estas quatro rotas estavam no blueprint de relatórios (routes/report_routes.py:157-223).
"""
from flask import Blueprint

from middlewares.auth import require_admin, require_auth


def criar_category_blueprint(controller):
    bp = Blueprint("categories", __name__)
    bp.add_url_rule("/categories", "list", require_auth(controller.listar), methods=["GET"])
    bp.add_url_rule("/categories", "create", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "/categories/<int:cat_id>", "update", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/categories/<int:cat_id>", "delete", require_admin(controller.deletar), methods=["DELETE"]
    )
    return bp
