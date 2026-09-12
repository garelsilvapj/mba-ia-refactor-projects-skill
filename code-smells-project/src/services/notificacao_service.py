"""Notificações do domínio de pedidos.

Antes: os envios eram `print` dentro do controller (controllers.py:208-210 e 248-250),
misturando efeito colateral com fluxo HTTP.

Aqui a notificação é uma dependência própria, substituível em teste e registrada via `logging`.
Os canais reais (e-mail, SMS, push) entram nesta classe sem tocar em controller nem service.
"""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("pedido criado", extra={"pedido_id": pedido_id, "usuario_id": usuario_id})

    def status_alterado(self, pedido_id, novo_status):
        logger.info(
            "status de pedido alterado",
            extra={"pedido_id": pedido_id, "status": novo_status},
        )
