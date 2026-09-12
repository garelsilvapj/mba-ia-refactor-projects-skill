from routes.category_routes import criar_category_blueprint
from routes.report_routes import criar_report_blueprint
from routes.system_routes import criar_system_blueprint
from routes.task_routes import criar_task_blueprint
from routes.user_routes import criar_user_blueprint

__all__ = [
    "criar_task_blueprint",
    "criar_user_blueprint",
    "criar_category_blueprint",
    "criar_report_blueprint",
    "criar_system_blueprint",
]
