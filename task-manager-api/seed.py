"""Popula o banco com dados iniciais.

Antes importava `app` do módulo, o que disparava `db.create_all()` como efeito colateral.
Agora cria a aplicação explicitamente pelo factory.
"""
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import now_utc_naive

USUARIOS = [
    ("João Silva", "joao@email.com", "1234", "admin"),
    ("Maria Santos", "maria@email.com", "abcd", "user"),
    ("Pedro Oliveira", "pedro@email.com", "pass", "manager"),
]

CATEGORIAS = [
    ("Backend", "Tarefas de backend", "#3498db"),
    ("Frontend", "Tarefas de frontend", "#2ecc71"),
    ("DevOps", "Tarefas de infraestrutura", "#e74c3c"),
    ("Bug", "Correção de bugs", "#e67e22"),
]


def _tarefas(agora, usuarios, categorias):
    return [
        {"title": "Implementar autenticação JWT", "description": "Adicionar autenticação real com JWT", "status": "pending", "priority": 1, "user_id": usuarios[0].id, "category_id": categorias[0].id, "due_date": agora - timedelta(days=3)},
        {"title": "Criar tela de login", "description": "Tela de login responsiva", "status": "in_progress", "priority": 2, "user_id": usuarios[1].id, "category_id": categorias[1].id, "due_date": agora + timedelta(days=5)},
        {"title": "Configurar CI/CD", "description": "Pipeline com GitHub Actions", "status": "done", "priority": 2, "user_id": usuarios[2].id, "category_id": categorias[2].id, "tags": "devops,ci,github"},
        {"title": "Corrigir bug no filtro de busca", "description": "Filtro não funciona com caracteres especiais", "status": "pending", "priority": 1, "user_id": usuarios[0].id, "category_id": categorias[3].id, "due_date": agora - timedelta(days=1)},
        {"title": "Adicionar paginação na API", "description": "Endpoints retornam todos os registros", "status": "pending", "priority": 3, "user_id": usuarios[0].id, "category_id": categorias[0].id, "due_date": agora + timedelta(days=10)},
        {"title": "Escrever testes unitários", "description": "Cobertura mínima de 80%", "status": "pending", "priority": 2, "user_id": usuarios[1].id, "category_id": categorias[0].id},
        {"title": "Documentar API com Swagger", "description": "Gerar documentação automática", "status": "cancelled", "priority": 4, "user_id": usuarios[2].id, "category_id": categorias[0].id},
        {"title": "Refatorar models", "description": "Melhorar organização dos models", "status": "in_progress", "priority": 3, "user_id": usuarios[1].id, "category_id": categorias[0].id, "tags": "refactor,tech-debt"},
        {"title": "Configurar monitoramento", "description": "Prometheus + Grafana", "status": "pending", "priority": 4, "user_id": usuarios[2].id, "category_id": categorias[2].id, "due_date": agora + timedelta(days=20)},
        {"title": "Melhorar validações de input", "description": "Usar marshmallow ou pydantic", "status": "pending", "priority": 3, "user_id": usuarios[0].id, "category_id": categorias[0].id, "tags": "improvement,validation"},
    ]


def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        usuarios = []
        for nome, email, senha, papel in USUARIOS:
            usuario = User()
            usuario.name = nome
            usuario.email = email
            usuario.set_password(senha)   # hash forte, não mais MD5
            usuario.role = papel
            db.session.add(usuario)
            usuarios.append(usuario)

        categorias = []
        for nome, descricao, cor in CATEGORIAS:
            categoria = Category()
            categoria.name = nome
            categoria.description = descricao
            categoria.color = cor
            db.session.add(categoria)
            categorias.append(categoria)

        db.session.commit()

        for dados in _tarefas(now_utc_naive(), usuarios, categorias):
            tarefa = Task()
            tarefa.title = dados["title"]
            tarefa.description = dados["description"]
            tarefa.status = dados["status"]
            tarefa.priority = dados["priority"]
            tarefa.user_id = dados["user_id"]
            tarefa.category_id = dados["category_id"]
            tarefa.due_date = dados.get("due_date")
            tarefa.tags = dados.get("tags")
            db.session.add(tarefa)

        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == "__main__":
    seed_data()
