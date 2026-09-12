"""Camada de rotas: mapeia URL → método de controller. Nenhuma lógica aqui.

Antes: as rotas eram declaradas com `add_url_rule` em app.py:11-30 (estilo pré-Blueprint) e
três handlers estavam implementados dentro do próprio app.py, incluindo os dois endpoints
administrativos sem autenticação.
"""
from flask import Blueprint

from src.middlewares.admin import require_admin


def criar_blueprints(controllers):
    produto = controllers["produto"]
    usuario = controllers["usuario"]
    pedido = controllers["pedido"]
    sistema = controllers["sistema"]
    admin = controllers["admin"]

    produtos_bp = Blueprint("produtos", __name__)
    # /produtos/busca antes de /produtos/<int:id> para não competir na resolução.
    produtos_bp.add_url_rule("/produtos", "listar", produto.listar, methods=["GET"])
    produtos_bp.add_url_rule("/produtos/busca", "buscar", produto.pesquisar, methods=["GET"])
    produtos_bp.add_url_rule("/produtos/<int:id>", "obter", produto.buscar, methods=["GET"])
    produtos_bp.add_url_rule("/produtos", "criar", produto.criar, methods=["POST"])
    produtos_bp.add_url_rule(
        "/produtos/<int:id>", "atualizar", produto.atualizar, methods=["PUT"]
    )
    produtos_bp.add_url_rule(
        "/produtos/<int:id>", "deletar", produto.deletar, methods=["DELETE"]
    )

    usuarios_bp = Blueprint("usuarios", __name__)
    usuarios_bp.add_url_rule("/usuarios", "listar", usuario.listar, methods=["GET"])
    usuarios_bp.add_url_rule("/usuarios/<int:id>", "obter", usuario.buscar, methods=["GET"])
    usuarios_bp.add_url_rule("/usuarios", "criar", usuario.criar, methods=["POST"])
    usuarios_bp.add_url_rule("/login", "login", usuario.login, methods=["POST"])

    pedidos_bp = Blueprint("pedidos", __name__)
    pedidos_bp.add_url_rule("/pedidos", "criar", pedido.criar, methods=["POST"])
    pedidos_bp.add_url_rule("/pedidos", "listar", pedido.listar_todos, methods=["GET"])
    pedidos_bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_do_usuario",
        pedido.listar_do_usuario,
        methods=["GET"],
    )
    pedidos_bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status",
        "atualizar_status",
        pedido.atualizar_status,
        methods=["PUT"],
    )

    sistema_bp = Blueprint("sistema", __name__)
    sistema_bp.add_url_rule("/", "index", sistema.index, methods=["GET"])
    sistema_bp.add_url_rule("/health", "health", sistema.health, methods=["GET"])
    sistema_bp.add_url_rule(
        "/relatorios/vendas", "relatorio_vendas", sistema.relatorio_vendas, methods=["GET"]
    )

    admin_bp = Blueprint("admin", __name__)
    # Rotas preservadas para não quebrar o contrato: /admin/reset-db segue funcionando (e pode
    # exigir credencial via ADMIN_TOKEN) e /admin/query responde 410, explicando a retirada.
    admin_bp.add_url_rule(
        "/admin/reset-db",
        "reset_db",
        require_admin(admin.resetar_banco),
        methods=["POST"],
    )
    admin_bp.add_url_rule(
        "/admin/query", "query", admin.executar_query, methods=["POST"]
    )

    return (produtos_bp, usuarios_bp, pedidos_bp, sistema_bp, admin_bp)
