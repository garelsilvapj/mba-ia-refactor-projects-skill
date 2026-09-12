"""Controller de usuário e login."""
from flask import jsonify, request


class UsuarioController:
    def __init__(self, usuario_service):
        self._service = usuario_service

    def listar(self):
        return jsonify({"dados": self._service.listar(), "sucesso": True}), 200

    def buscar(self, id):
        return jsonify({"dados": self._service.buscar(id), "sucesso": True}), 200

    def criar(self):
        usuario_id = self._service.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        usuario = self._service.autenticar(request.get_json(silent=True))
        return (
            jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}),
            200,
        )
