"""Relatórios de produtividade.

Antes `summary_report` tinha 90 linhas dentro da rota (routes/report_routes.py:12-101), com
nove contagens independentes, uma consulta por usuário e o cálculo de atraso em Python sobre
todas as tarefas.
"""
from datetime import timedelta

from sqlalchemy import case, func, select

from middlewares.errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import now_utc_naive
from utils.helpers import calcular_percentual, formatar_data

DIAS_RECENTES = 7
PRIORIDADE_ROTULOS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}
PRIORIDADE_ALTA_ATE = 2


class ReportService:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def resumo(self):
        agora = now_utc_naive()
        corte_recente = agora - timedelta(days=DIAS_RECENTES)

        por_status = dict(
            self.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
        )
        por_prioridade = dict(
            self.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all()
        )

        totais = self.session.execute(
            select(
                select(func.count()).select_from(Task).scalar_subquery(),
                select(func.count()).select_from(User).scalar_subquery(),
                select(func.count()).select_from(Category).scalar_subquery(),
            )
        ).one()

        atrasadas = (
            self.session.execute(
                select(Task).where(self._condicao_atraso(agora)).order_by(Task.id)
            )
            .scalars()
            .all()
        )

        recentes_criadas = self.session.execute(
            select(func.count()).select_from(Task).where(Task.created_at >= corte_recente)
        ).scalar_one()
        recentes_concluidas = self.session.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.status == "done", Task.updated_at >= corte_recente)
        ).scalar_one()

        return {
            "generated_at": str(agora),
            "overview": {
                "total_tasks": totais[0],
                "total_users": totais[1],
                "total_categories": totais[2],
            },
            "tasks_by_status": {
                status: por_status.get(status, 0) for status in self.config.STATUSES_VALIDOS
            },
            "tasks_by_priority": {
                rotulo: por_prioridade.get(prioridade, 0)
                for prioridade, rotulo in PRIORIDADE_ROTULOS.items()
            },
            "overdue": {
                "count": len(atrasadas),
                "tasks": [
                    {
                        "id": tarefa.id,
                        "title": tarefa.title,
                        "due_date": formatar_data(tarefa.due_date),
                        "days_overdue": (agora - tarefa.due_date).days,
                    }
                    for tarefa in atrasadas
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": recentes_criadas,
                "tasks_completed_last_7_days": recentes_concluidas,
            },
            "user_productivity": self._produtividade_por_usuario(),
        }

    def por_usuario(self, user_id):
        usuario = self.session.get(User, user_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")

        agora = now_utc_naive()
        linha = self.session.execute(
            select(
                func.count(),
                func.sum(case((Task.status == "done", 1), else_=0)),
                func.sum(case((Task.status == "pending", 1), else_=0)),
                func.sum(case((Task.status == "in_progress", 1), else_=0)),
                func.sum(case((Task.status == "cancelled", 1), else_=0)),
                func.sum(case((Task.priority <= PRIORIDADE_ALTA_ATE, 1), else_=0)),
                func.sum(case((self._condicao_atraso(agora), 1), else_=0)),
            ).where(Task.user_id == user_id)
        ).one()

        total = linha[0] or 0
        concluidas = linha[1] or 0
        return {
            "user": {"id": usuario.id, "name": usuario.name, "email": usuario.email},
            "statistics": {
                "total_tasks": total,
                "done": concluidas,
                "pending": linha[2] or 0,
                "in_progress": linha[3] or 0,
                "cancelled": linha[4] or 0,
                "overdue": linha[6] or 0,
                "high_priority": linha[5] or 0,
                "completion_rate": calcular_percentual(concluidas, total),
            },
        }

    # --- apoio ---

    @staticmethod
    def _condicao_atraso(agora):
        """Tradução em SQL da mesma regra de `Task.is_overdue()`."""
        return (
            Task.due_date.is_not(None)
            & (Task.due_date < agora)
            & Task.status.not_in(("done", "cancelled"))
        )

    def _produtividade_por_usuario(self):
        """Uma consulta agregada — antes era uma consulta de tarefas por usuário, em laço."""
        linhas = self.session.execute(
            select(
                User.id,
                User.name,
                func.count(Task.id),
                func.sum(case((Task.status == "done", 1), else_=0)),
            )
            .select_from(User)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
        ).all()

        produtividade = []
        for user_id, nome, total, concluidas in linhas:
            total = total or 0
            concluidas = concluidas or 0
            produtividade.append(
                {
                    "user_id": user_id,
                    "user_name": nome,
                    "total_tasks": total,
                    "completed_tasks": concluidas,
                    "completion_rate": calcular_percentual(concluidas, total),
                }
            )
        return produtividade
