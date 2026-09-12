"""Regra de negócio de categorias.

Antes estas quatro operações estavam no blueprint de relatórios
(routes/report_routes.py:157-223), recurso que nada tinha a ver com relatório.
"""
from sqlalchemy import func, select

from middlewares.errors import NotFoundError
from models.category import Category
from models.task import Task


class CategoryService:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def listar(self):
        """Uma consulta agregada — antes era uma contagem por categoria dentro do laço."""
        contagens = dict(
            self.session.execute(
                select(Task.category_id, func.count())
                .where(Task.category_id.is_not(None))
                .group_by(Task.category_id)
            ).all()
        )
        categorias = self.session.execute(select(Category).order_by(Category.id)).scalars().all()
        return [
            {**categoria.to_dict(), "task_count": contagens.get(categoria.id, 0)}
            for categoria in categorias
        ]

    def buscar(self, categoria_id):
        categoria = self.session.get(Category, categoria_id)
        if categoria is None:
            raise NotFoundError("Categoria não encontrada")
        return categoria

    def criar(self, dados):
        categoria = Category()
        categoria.name = dados["name"]
        categoria.description = dados.get("description", "")
        categoria.color = dados.get("color", self.config.COR_PADRAO)

        self.session.add(categoria)
        self.session.commit()
        return categoria.to_dict()

    def atualizar(self, categoria_id, dados):
        categoria = self.buscar(categoria_id)
        for campo in ("name", "description", "color"):
            if campo in dados:
                setattr(categoria, campo, dados[campo])
        self.session.commit()
        return categoria.to_dict()

    def deletar(self, categoria_id):
        categoria = self.buscar(categoria_id)
        self.session.delete(categoria)
        self.session.commit()
        return {"message": "Categoria deletada"}
