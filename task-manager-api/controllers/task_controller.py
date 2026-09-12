"""Controller de tarefas: entrada → service → resposta. Sem ORM e sem regra de negócio."""
from flask import jsonify, request

from schemas import TaskCreateSchema, TaskSearchSchema, TaskUpdateSchema


class TaskController:
    def __init__(self, task_service):
        self.service = task_service
        self.schema_criacao = TaskCreateSchema()
        self.schema_atualizacao = TaskUpdateSchema()
        self.schema_busca = TaskSearchSchema()

    def listar(self):
        return jsonify(self.service.listar()), 200

    def detalhar(self, task_id):
        return jsonify(self.service.detalhar(task_id)), 200

    def criar(self):
        dados = self.schema_criacao.carregar(request.get_json(silent=True))
        return jsonify(self.service.criar(dados)), 201

    def atualizar(self, task_id):
        dados = self.schema_atualizacao.carregar(request.get_json(silent=True))
        return jsonify(self.service.atualizar(task_id, dados)), 200

    def deletar(self, task_id):
        return jsonify(self.service.deletar(task_id)), 200

    def pesquisar(self):
        filtros = self.schema_busca.carregar(request.args.to_dict())
        return jsonify(self.service.pesquisar(filtros)), 200

    def estatisticas(self):
        return jsonify(self.service.estatisticas()), 200
