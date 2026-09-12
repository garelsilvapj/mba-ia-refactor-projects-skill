"""Regra de negócio de tarefas.

Antes tudo isto vivia dentro dos handlers de rota (routes/task_routes.py:11-299), junto com as
consultas ao ORM, a serialização e a lógica de atraso copiada de outros arquivos.
"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from middlewares.errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import now_utc_naive
from utils.helpers import escapar_like


class TaskService:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    # --- leitura ---

    def listar(self):
        """Carrega usuário e categoria junto — antes eram duas consultas por tarefa."""
        tarefas = (
            self.session.execute(
                select(Task)
                .options(selectinload(Task.user), selectinload(Task.category))
                .order_by(Task.id)
            )
            .scalars()
            .all()
        )
        return [self._com_relacionamentos(tarefa) for tarefa in tarefas]

    def buscar(self, task_id):
        tarefa = self.session.get(Task, task_id)
        if tarefa is None:
            raise NotFoundError("Task não encontrada")
        return tarefa

    def detalhar(self, task_id):
        tarefa = self.buscar(task_id)
        dados = tarefa.to_dict()
        dados["overdue"] = tarefa.is_overdue()
        return dados

    def pesquisar(self, filtros):
        consulta = select(Task)
        termo = filtros.get("q")
        if termo:
            padrao = f"%{escapar_like(termo)}%"
            consulta = consulta.where(
                Task.title.like(padrao, escape="\\") | Task.description.like(padrao, escape="\\")
            )
        if filtros.get("status"):
            consulta = consulta.where(Task.status == filtros["status"])
        if filtros.get("priority") is not None:
            consulta = consulta.where(Task.priority == filtros["priority"])
        if filtros.get("user_id") is not None:
            consulta = consulta.where(Task.user_id == filtros["user_id"])

        consulta = consulta.order_by(Task.id)
        if filtros.get("limit"):
            consulta = consulta.limit(filtros["limit"]).offset(filtros.get("offset", 0))

        tarefas = self.session.execute(consulta).scalars().all()
        return [tarefa.to_dict() for tarefa in tarefas]

    def estatisticas(self):
        """Contagens agregadas no banco — antes eram cinco consultas mais um laço em Python."""
        por_status = dict(
            self.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
        )
        total = sum(por_status.values())
        concluidas = por_status.get("done", 0)

        atrasadas = self.session.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.due_date.is_not(None),
                Task.due_date < now_utc_naive(),
                Task.status.not_in(("done", "cancelled")),
            )
        ).scalar_one()

        return {
            "total": total,
            "pending": por_status.get("pending", 0),
            "in_progress": por_status.get("in_progress", 0),
            "done": concluidas,
            "cancelled": por_status.get("cancelled", 0),
            "overdue": atrasadas,
            "completion_rate": round((concluidas / total) * 100, 2) if total > 0 else 0,
        }

    def listar_do_usuario(self, user_id):
        tarefas = (
            self.session.execute(
                select(Task).where(Task.user_id == user_id).order_by(Task.id)
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": tarefa.id,
                "title": tarefa.title,
                "description": tarefa.description,
                "status": tarefa.status,
                "priority": tarefa.priority,
                "created_at": str(tarefa.created_at),
                "due_date": str(tarefa.due_date) if tarefa.due_date else None,
                "overdue": tarefa.is_overdue(),
            }
            for tarefa in tarefas
        ]

    # --- escrita ---

    def criar(self, dados):
        self._validar_referencias(dados)

        tarefa = Task()
        tarefa.title = dados["title"]
        tarefa.description = dados.get("description", "")
        tarefa.status = dados["status"]
        tarefa.priority = dados["priority"]
        tarefa.user_id = dados.get("user_id")
        tarefa.category_id = dados.get("category_id")
        tarefa.due_date = self._data(dados.get("due_date"))
        tarefa.set_tags(dados.get("tags"))

        self.session.add(tarefa)
        self.session.commit()
        return tarefa.to_dict()

    def atualizar(self, task_id, dados):
        tarefa = self.buscar(task_id)
        self._validar_referencias(dados)

        for campo in ("title", "description", "status", "priority"):
            if campo in dados:
                setattr(tarefa, campo, dados[campo])
        if "user_id" in dados:
            tarefa.user_id = dados["user_id"]
        if "category_id" in dados:
            tarefa.category_id = dados["category_id"]
        if "due_date" in dados:
            tarefa.due_date = self._data(dados["due_date"])
        if "tags" in dados:
            tarefa.set_tags(dados["tags"])

        self.session.commit()
        return tarefa.to_dict()

    def deletar(self, task_id):
        tarefa = self.buscar(task_id)
        self.session.delete(tarefa)
        self.session.commit()
        return {"message": "Task deletada com sucesso"}

    # --- apoio ---

    def _validar_referencias(self, dados):
        if dados.get("user_id") and self.session.get(User, dados["user_id"]) is None:
            raise NotFoundError("Usuário não encontrado")
        if dados.get("category_id") and self.session.get(Category, dados["category_id"]) is None:
            raise NotFoundError("Categoria não encontrada")

    @staticmethod
    def _data(valor):
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor
        # marshmallow entrega `date`; a coluna é DateTime, como antes.
        return datetime(valor.year, valor.month, valor.day)

    @staticmethod
    def _com_relacionamentos(tarefa):
        dados = tarefa.to_dict()
        dados["overdue"] = tarefa.is_overdue()
        dados["user_name"] = tarefa.user.name if tarefa.user else None
        dados["category_name"] = tarefa.category.name if tarefa.category else None
        return dados

