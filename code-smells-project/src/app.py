"""Composition root: cria a aplicação e liga as camadas.

É o único lugar que sabe montar o grafo de dependências. Models, services e controllers
recebem o que precisam por parâmetro, então qualquer camada pode ser testada com um dublê.
"""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Config
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.errors import register_error_handlers
from src.models.db import close_db, get_db, init_db
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.admin_service import AdminService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import criar_blueprints

logger = logging.getLogger(__name__)


def montar_dependencias(config, conexao_provider=get_db):
    """Instancia models, services e controllers. Recebe o provedor de conexão por parâmetro."""
    produto_model = ProdutoModel(conexao_provider)
    usuario_model = UsuarioModel(conexao_provider)
    pedido_model = PedidoModel(conexao_provider)

    notificador = NotificacaoService()
    produto_service = ProdutoService(produto_model, config)
    usuario_service = UsuarioService(usuario_model, config)
    pedido_service = PedidoService(pedido_model, produto_model, config, notificador)
    relatorio_service = RelatorioService(pedido_model, config)

    return {
        "produto": ProdutoController(produto_service),
        "usuario": UsuarioController(usuario_service),
        "pedido": PedidoController(pedido_service),
        "sistema": SistemaController(
            relatorio_service, produto_model, usuario_model, pedido_model
        ),
        "admin": AdminController(AdminService(conexao_provider)),
    }


def create_app(config=Config, inicializar_banco=True):
    """App factory: sem efeito colateral em import, uma instância isolada por chamada."""
    logging.basicConfig(
        level=logging.DEBUG if config.DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.config.from_object(config)

    if not getattr(config, "SECRET_KEY_FROM_ENV", True):
        logger.warning(
            "SECRET_KEY não definida no ambiente: usando chave aleatória desta execução. "
            "Defina SECRET_KEY no .env para manter sessões válidas entre reinícios."
        )

    # CORS restrito às origens configuradas, não mais liberado para qualquer origem.
    CORS(app, origins=config.CORS_ORIGINS)

    if inicializar_banco:
        init_db(config.DB_PATH)

    # Conexão por requisição: fechada ao final de cada uma.
    app.teardown_appcontext(close_db)

    for blueprint in criar_blueprints(montar_dependencias(config)):
        app.register_blueprint(blueprint)

    register_error_handlers(app)
    return app
