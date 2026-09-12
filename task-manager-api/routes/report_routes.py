"""Rotas de relatórios."""
from flask import Blueprint

from middlewares.auth import require_admin, require_auth


def criar_report_blueprint(controller):
    bp = Blueprint("reports", __name__)
    # O resumo expõe a produtividade de toda a equipe: restrito a administradores.
    bp.add_url_rule(
        "/reports/summary", "summary", require_admin(controller.resumo), methods=["GET"]
    )
    bp.add_url_rule(
        "/reports/user/<int:user_id>",
        "user",
        require_auth(controller.por_usuario),
        methods=["GET"],
    )
    return bp
