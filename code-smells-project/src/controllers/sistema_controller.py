"""Controller de rotas de sistema: índice, health check e relatório de vendas."""
from flask import current_app, jsonify


class SistemaController:
    def __init__(self, relatorio_service, produto_model, usuario_model, pedido_model):
        self._relatorios = relatorio_service
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def index(self):
        return (
            jsonify(
                {
                    "mensagem": "Bem-vindo à API da Loja",
                    "versao": current_app.config["VERSAO"],
                    "endpoints": {
                        "produtos": "/produtos",
                        "usuarios": "/usuarios",
                        "pedidos": "/pedidos",
                        "login": "/login",
                        "relatorios": "/relatorios/vendas",
                        "health": "/health",
                    },
                }
            ),
            200,
        )

    def health(self):
        # [corrige CRITICAL] antes (controllers.py:285-289) esta resposta devolvia secret_key,
        # db_path, debug e ambiente. Agora só reporta o estado do serviço e das dependências.
        return (
            jsonify(
                {
                    "status": "ok",
                    "database": "connected",
                    "counts": {
                        "produtos": self._produtos.contar(),
                        "usuarios": self._usuarios.contar(),
                        "pedidos": self._pedidos.contar(),
                    },
                    "versao": current_app.config["VERSAO"],
                }
            ),
            200,
        )

    def relatorio_vendas(self):
        return jsonify({"dados": self._relatorios.vendas(), "sucesso": True}), 200
