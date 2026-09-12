"""Model de usuário.

Correções em relação à versão anterior:
  - senha com hash forte (werkzeug/scrypt) no lugar de MD5 sem salt;
  - `to_dict()` não devolve mais o campo `password`;
  - `is_admin()` volta a ter uso real, no middleware de autorização.
"""
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.clock import now_utc_naive


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc_naive)

    def to_dict(self):
        """Serialização pública: allowlist de campos, sem o hash da senha."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, senha):
        # Antes: hashlib.md5(...).hexdigest() — sem salt e reversível por rainbow table.
        self.password = generate_password_hash(senha)

    def check_password(self, senha):
        # Comparação em tempo constante, feita pela própria werkzeug.
        return check_password_hash(self.password, senha)

    def is_admin(self):
        return self.role == "admin"
