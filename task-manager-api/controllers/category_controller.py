"""Controller de categorias."""
from flask import jsonify, request

from schemas import CategoryCreateSchema, CategoryUpdateSchema


class CategoryController:
    def __init__(self, category_service):
        self.service = category_service
        self.schema_criacao = CategoryCreateSchema()
        self.schema_atualizacao = CategoryUpdateSchema()

    def listar(self):
        return jsonify(self.service.listar()), 200

    def criar(self):
        dados = self.schema_criacao.carregar(request.get_json(silent=True))
        return jsonify(self.service.criar(dados)), 201

    def atualizar(self, cat_id):
        dados = self.schema_atualizacao.carregar(request.get_json(silent=True))
        return jsonify(self.service.atualizar(cat_id, dados)), 200

    def deletar(self, cat_id):
        return jsonify(self.service.deletar(cat_id)), 200
