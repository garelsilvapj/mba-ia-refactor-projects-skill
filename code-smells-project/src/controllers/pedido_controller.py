"""Controller de pedido."""
from flask import jsonify, request


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def criar(self):
        resultado = self._service.criar(request.get_json(silent=True))
        return (
            jsonify(
                {
                    "dados": resultado,
                    "sucesso": True,
                    "mensagem": "Pedido criado com sucesso",
                }
            ),
            201,
        )

    def listar_todos(self):
        return jsonify({"dados": self._service.listar(), "sucesso": True}), 200

    def listar_do_usuario(self, usuario_id):
        return jsonify({"dados": self._service.listar(usuario_id), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        corpo = request.get_json(silent=True) or {}
        self._service.atualizar_status(pedido_id, corpo.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
