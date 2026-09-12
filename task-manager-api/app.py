"""Task Manager API — composition root e entry point.

Antes este arquivo criava a aplicação no escopo do módulo, fixava SECRET_KEY e URI do banco no
código e chamava `db.create_all()` em tempo de import (app.py:30-31), o que disparava a criação
do banco só de importar o módulo.

Agora é um app factory: nada acontece na importação, a configuração vem do ambiente e as
dependências são montadas em um único lugar.
"""
import logging

from flask import Flask
from flask_cors import CORS

from config import Config
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.system_controller import SystemController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.errors import register_error_handlers
from routes import (
    criar_category_blueprint,
    criar_report_blueprint,
    criar_system_blueprint,
    criar_task_blueprint,
    criar_user_blueprint,
)
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.notification_service import NotificationService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService

logger = logging.getLogger(__name__)


def montar_blueprints(config):
    """Instancia services e controllers com a sessão do SQLAlchemy e devolve os blueprints."""
    sessao = db.session

    task_service = TaskService(sessao, config)
    user_service = UserService(sessao, config)
    auth_service = AuthService(sessao, config)
    category_service = CategoryService(sessao, config)
    report_service = ReportService(sessao, config)
    NotificationService(config)  # disponível para os services que precisarem notificar

    return (
        criar_system_blueprint(SystemController()),
        criar_task_blueprint(TaskController(task_service)),
        criar_user_blueprint(UserController(user_service, auth_service, task_service)),
        criar_category_blueprint(CategoryController(category_service)),
        criar_report_blueprint(ReportController(report_service)),
    )


def create_app(config=Config, criar_tabelas=True):
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.config.from_object(config)

    if not getattr(config, "SECRET_KEY_FROM_ENV", True):
        logger.warning(
            "SECRET_KEY não definida no ambiente: usando chave aleatória desta execução. "
            "Os tokens emitidos deixam de valer a cada reinício."
        )

    CORS(app, origins=config.CORS_ORIGINS)
    db.init_app(app)

    for blueprint in montar_blueprints(config):
        app.register_blueprint(blueprint)

    register_error_handlers(app)

    if criar_tabelas:
        # Explícito, e não mais como efeito colateral de importar o módulo.
        with app.app_context():
            db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
