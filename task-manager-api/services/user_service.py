"""Regra de negócio de usuários.

Antes esta lógica estava dentro de routes/user_routes.py:42-151, com validações inline
duplicadas entre criação e atualização.
"""
from sqlalchemy import func, select

from middlewares.errors import ConflictError, NotFoundError
from models.task import Task
from models.user import User


class UserService:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    # --- leitura ---

    def listar(self):
        """Conta as tarefas por usuário no banco — antes era `len(u.tasks)`, uma consulta cada."""
        contagens = dict(
            self.session.execute(
                select(Task.user_id, func.count()).where(Task.user_id.is_not(None)).group_by(Task.user_id)
            ).all()
        )
        usuarios = self.session.execute(select(User).order_by(User.id)).scalars().all()
        return [
            {**usuario.to_dict(), "task_count": contagens.get(usuario.id, 0)}
            for usuario in usuarios
        ]

    def buscar(self, user_id):
        usuario = self.session.get(User, user_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def detalhar(self, user_id):
        usuario = self.buscar(user_id)
        tarefas = (
            self.session.execute(select(Task).where(Task.user_id == user_id).order_by(Task.id))
            .scalars()
            .all()
        )
        dados = usuario.to_dict()
        dados["tasks"] = [tarefa.to_dict() for tarefa in tarefas]
        return dados

    # --- escrita ---

    def criar(self, dados, papel_permitido=True):
        self._garantir_email_livre(dados["email"])

        usuario = User()
        usuario.name = dados["name"]
        usuario.email = dados["email"]
        usuario.set_password(dados["password"])
        # Registro público não escolhe o próprio papel: sem privilégio, entra como 'user'.
        usuario.role = dados.get("role", self.config.ROLE_PADRAO) if papel_permitido else self.config.ROLE_PADRAO

        self.session.add(usuario)
        self.session.commit()
        return usuario.to_dict()

    def atualizar(self, user_id, dados):
        usuario = self.buscar(user_id)

        if "email" in dados:
            self._garantir_email_livre(dados["email"], ignorar_id=user_id)
            usuario.email = dados["email"]
        if "name" in dados:
            usuario.name = dados["name"]
        if "password" in dados:
            usuario.set_password(dados["password"])
        if "role" in dados:
            usuario.role = dados["role"]
        if "active" in dados:
            usuario.active = dados["active"]

        self.session.commit()
        return usuario.to_dict()

    def deletar(self, user_id):
        """Exclusão do usuário e de suas tarefas na mesma transação."""
        usuario = self.buscar(user_id)
        try:
            tarefas = (
                self.session.execute(select(Task).where(Task.user_id == user_id)).scalars().all()
            )
            for tarefa in tarefas:
                self.session.delete(tarefa)
            self.session.delete(usuario)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return {"message": "Usuário deletado com sucesso"}

    # --- apoio ---

    def _garantir_email_livre(self, email, ignorar_id=None):
        existente = self.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existente is not None and existente.id != ignorar_id:
            raise ConflictError("Email já cadastrado")
