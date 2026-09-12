"""Controller de usuários e login."""
from flask import g, jsonify, request

from schemas import LoginSchema, UserCreateSchema, UserUpdateSchema


class UserController:
    def __init__(self, user_service, auth_service, task_service):
        self.users = user_service
        self.auth = auth_service
        self.tasks = task_service
        self.schema_criacao = UserCreateSchema()
        self.schema_atualizacao = UserUpdateSchema()
        self.schema_login = LoginSchema()

    def listar(self):
        return jsonify(self.users.listar()), 200

    def detalhar(self, user_id):
        return jsonify(self.users.detalhar(user_id)), 200

    def criar(self):
        dados = self.schema_criacao.carregar(request.get_json(silent=True))
        # Só um administrador autenticado escolhe o papel do novo usuário.
        solicitante = getattr(g, "usuario", None)
        pode_definir_papel = solicitante is not None and solicitante.is_admin()
        return jsonify(self.users.criar(dados, papel_permitido=pode_definir_papel)), 201

    def atualizar(self, user_id):
        dados = self.schema_atualizacao.carregar(request.get_json(silent=True))
        return jsonify(self.users.atualizar(user_id, dados)), 200

    def deletar(self, user_id):
        return jsonify(self.users.deletar(user_id)), 200

    def tarefas_do_usuario(self, user_id):
        self.users.buscar(user_id)  # 404 se o usuário não existir
        return jsonify(self.tasks.listar_do_usuario(user_id)), 200

    def login(self):
        dados = self.schema_login.carregar(request.get_json(silent=True))
        return jsonify(self.auth.login(dados)), 200
