"""Model de tarefa.

`is_overdue()` já existia e nunca era chamado, enquanto a mesma regra estava copiada em cinco
rotas. Agora é a única implementação e é usada por toda a aplicação.
"""
from database import db
from utils.clock import now_utc_naive

TAG_SEPARADOR = ","


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc_naive)
    updated_at = db.Column(db.DateTime, default=now_utc_naive, onupdate=now_utc_naive)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tags.split(TAG_SEPARADOR) if self.tags else [],
        }

    def is_overdue(self):
        """Única definição de 'atrasada': tem prazo vencido e não está concluída nem cancelada."""
        if not self.due_date:
            return False
        if self.status in ("done", "cancelled"):
            return False
        return self.due_date < now_utc_naive()

    def set_tags(self, tags):
        if tags is None:
            self.tags = None
        elif isinstance(tags, list):
            self.tags = TAG_SEPARADOR.join(str(tag) for tag in tags)
        else:
            self.tags = tags
